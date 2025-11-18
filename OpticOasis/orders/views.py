from userpanel.models import UserAddress ,Wallet ,WalletTransaction
from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import OrderMain, OrderSub ,ReturnRequest ,OrderAddress
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse ,HttpResponseRedirect
from django.utils.crypto import get_random_string
from utils.decorators import admin_required
from django.core.paginator import Paginator
from cart.models import CartItem, Cart
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from coupon.models import Coupon
from django.conf import settings
from django.urls import reverse
from datetime import timedelta
from decimal import Decimal
import razorpay
import uuid

# Create your views here.

@admin_required
def admin_order_list(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'Show all')
    items_per_page = request.GET.get('items_per_page', 15)


    orders = OrderMain.objects.all().order_by('-id')
    if search_query:
        orders = orders.filter(order_id__icontains=search_query)
    if status_filter != 'Show all':
        orders = orders.filter(order_status=status_filter)


    paginator = Paginator(orders, items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'items_per_page': items_per_page,
        'ORDER_STATUS_CHOICES': OrderMain.ORDER_STATUS_CHOICES,
    }
    return render(request, 'admin_side/order/order_list.html', context)


@admin_required
def returned_orders(request):
    search_query = request.GET.get('search', '')
    items_per_page = int(request.GET.get('items_per_page', 10))

    orders = OrderMain.objects.filter(returnrequest__isnull=False).distinct()
    
    if search_query:
        orders = orders.filter(order_id__icontains=search_query)

    order_list = []
    for order in orders:
        return_requests = ReturnRequest.objects.filter(order_main=order).order_by('-id')
        if return_requests.exists():
            latest_return_id = return_requests.first().id 
        else:
            latest_return_id = 0

        has_pending_returns = return_requests.filter(status='Pending').exists()
        order_list.append({
            'order': order,
            'has_pending_returns': has_pending_returns,
            'return_requests': return_requests,
            'latest_return_id': latest_return_id,
        })

    order_list = sorted(order_list, key=lambda x: x['latest_return_id'], reverse=True)


    paginator = Paginator(order_list, items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'items_per_page': str(items_per_page), 
    }

    return render(request, 'admin_side/order/return_order.html', context)

@admin_required
def admin_orders_details(request, oid):
    order = get_object_or_404(OrderMain, pk=oid)
    order_items = OrderSub.objects.filter(main_order=order)
    return render(request, 'admin_side/order/order_detail.html', {'orders': order, 'order_sub': order_items})


@admin_required
def change_order_status(request, order_id):
    order = get_object_or_404(OrderMain, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('order_status')

        current_status = order.order_status
        invalid_transitions = {
            'Awaiting payment': ['Pending'],
            'Confirmed': ['Pending', 'Awaiting payment'],
            'Shipped': ['Confirmed', 'Awaiting payment', 'Pending'],
            'Delivered': ['Shipped', 'Confirmed', 'Awaiting payment', 'Pending'],
            'Canceled': [status for status, _ in OrderMain.ORDER_STATUS_CHOICES] ,
            'Returned': [status for status, _ in OrderMain.ORDER_STATUS_CHOICES]
        }

        if new_status == 'Returned':
            messages.error(request, 'Order status cannot be changed to Returned directly by the admin.')
        elif current_status in invalid_transitions and new_status in invalid_transitions[current_status]:
            messages.error(request, f'Cannot change status from {current_status} to {new_status}.')
        else:
            order.order_status = new_status
            if new_status == 'Delivered' and not order.payment_status:
                order.payment_status = True 
            if new_status == 'Canceled' and order.payment_status:
                refund_amount = order.final_amount
                wallet, created = Wallet.objects.get_or_create(user=order.user)
                wallet.balance += refund_amount 
                wallet.save()
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=refund_amount,
                    description=f'Refund for order {order.order_id}',
                    transaction_type='credit' 
                )

            order.save()
            messages.success(request, 'Order status updated successfully.')
        
    return redirect('orders:admin-orders-details', oid=order.id)


@admin_required
def update_return_request(request, return_request_id):
    return_request = get_object_or_404(ReturnRequest, id=return_request_id)
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "approve":
            return_request.status = "Approved"
            return_request.save()
            
            refund_amount = Decimal('0.00')
            
            if return_request.order_sub: 
                item = return_request.order_sub
                main_order = item.main_order
                item_total_cost = Decimal(str(item.total_cost()))
                order_total_amount = Decimal(str(main_order.total_amount))
                order_discount_amount = Decimal(str(main_order.discount_amount))
                
                item_discount_amount = (order_discount_amount * item_total_cost) / order_total_amount
                refund_amount = item_total_cost - item_discount_amount
                
                item.is_active = False
                item.status='Returned'
                item.save()
                all_canceled = not main_order.ordersub_set.filter(is_active=True).exists()
                
                if all_canceled:
                    main_order.order_status = 'Returned'
                    main_order.save()
                    
            else:
                order = return_request.order_main
                active_items = order.ordersub_set.filter(is_active=True)
                
                for item in active_items:
                    item_total_cost = Decimal(str(item.total_cost()))
                    order_total_amount = Decimal(str(order.total_amount))
                    order_discount_amount = Decimal(str(order.discount_amount))
                    
                    item_discount_amount = (order_discount_amount * item_total_cost) / order_total_amount
                    item_refund_amount = item_total_cost - item_discount_amount
                    
                    refund_amount += item_refund_amount
                    item.is_active = False
                    item.status='Returned'
                    item.save()

                order.order_status = 'Returned'
                order.is_active = False
                order.save()

            if refund_amount > 0 and return_request.order_main.payment_status:
                wallet, created = Wallet.objects.get_or_create(user=return_request.order_main.user)
                wallet.balance += refund_amount
                wallet.updated_at = timezone.now()
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=float(refund_amount),
                    description=f"Refund for {'order' if return_request.order_sub is None else 'item'} {return_request.order_main.order_id if return_request.order_sub is None else return_request.order_sub.variant.product.product_name}",
                    transaction_type='credit'
                )
                messages.success(request, f'Return request approved and amount credited to the user\'s wallet.')
            else:
                messages.success(request, 'Return request approved. No payment was made or payment status is not confirmed.')

        elif action == "reject":
            if return_request.order_sub: 
                item = return_request.order_sub
                item.status='Return Rejected'
                item.main_order.order_status='Return Rejected'
            else:
                order = return_request.order_main
                active_items = order.ordersub_set.filter(is_active=True)
                for item in active_items:
                    item.status='Return Rejected'
                    item.save()
                order.order_status = 'Return Rejected'
                order.save()    
            return_request.status = "Rejected"
            return_request.save()
            messages.success(request, 'Return request rejected.')
        
        return redirect('orders:returned-orders') 


#user side order fuctions

def generate_unique_order_id():
    return str(uuid.uuid4())


def order_placed(request):
    if request.method == "POST":
        try:
            user = request.user
            cart_item_ids = request.POST.get('cart_item_ids', '')
            selected_address_id = request.POST.get('selected_address')
            payment_method = request.POST.get('payment_method')

            if not cart_item_ids:
                messages.error(request, "Cart is empty.")
                return redirect(f'{reverse("cart:checkout")}?cart_items={",".join(cart_item_ids)}&selected_address={selected_address_id}')

            cart_item_ids = cart_item_ids.split(',')
            cart_items = CartItem.objects.filter(id__in=cart_item_ids, cart__user=user)

            if not cart_items.exists():
                messages.error(request, "No valid items found. Please try again.")
                return redirect(f'{reverse("cart:checkout")}?cart_items={",".join(cart_item_ids)}&selected_address={selected_address_id}')

            for item in cart_items:
                if item.quantity > item.variant.variant_stock:
                    messages.error(request, f"Insufficient stock for {item.product.product_name}.")
                    return redirect(f'{reverse("cart:checkout")}?cart_items={",".join(cart_item_ids)}&selected_address={selected_address_id}')

                if not item.product.is_active or not item.variant.variant_status:
                    messages.error(request, f"{item.product.product_name} is no longer available.")
                    return redirect(f'{reverse("cart:checkout")}?cart_items={",".join(cart_item_ids)}&selected_address={selected_address_id}')

            user_address = UserAddress.objects.get(id=selected_address_id)


            with transaction.atomic():  

                order_address = OrderAddress.objects.create(
                    name=user_address.name,
                    phone_number=user_address.phone_number,
                    house_name=user_address.house_name,
                    street_name=user_address.street_name,
                    district=user_address.district,
                    state=user_address.state,
                    country=user_address.country,
                    pin_number=user_address.pin_number
                )

                total_amount = sum(item.sub_total() for item in cart_items)
                discount_amount = Decimal(0)

                coupon_id = request.session.get('applied_coupon')
                if coupon_id:
                    try:
                        coupon = Coupon.objects.get(id=coupon_id)
                        discount_percentage = Decimal(coupon.discount) / Decimal(100)
                        calculated_discount = total_amount * discount_percentage
                        discount_amount = min(calculated_discount, coupon.maximum_amount)
                    except Coupon.DoesNotExist:
                        pass

                final_amount = total_amount - discount_amount

                if payment_method == 'cash_on_delivery':
                    if final_amount > 5000 :
                        messages.error(request, "Cash on Delivery is not available for orders above ₹5000.")
                        return redirect(f'{reverse("cart:checkout")}?cart_items={",".join(cart_item_ids)}&selected_address={selected_address_id}')
                    
                if payment_method == 'wallet':
                    wallet = Wallet.objects.get(user=user)
                    if wallet.balance < final_amount:
                        messages.error(request, "Insufficient wallet balance.")
                        return redirect(f'{reverse("cart:checkout")}?cart_items={",".join(cart_item_ids)}&selected_address={selected_address_id}')

                # creating main order inside atomic block
                order = OrderMain.objects.create(
                    user=user,
                    address=order_address,
                    total_amount=total_amount,
                    discount_amount=discount_amount,
                    final_amount=final_amount,
                    payment_option=payment_method,
                    order_id=generate_unique_order_id(),
                    payment_status=False,
                )
                
                for item in cart_items:
                    OrderSub.objects.create(
                        user=user,
                        main_order=order,
                        variant=item.variant,
                        quantity=item.quantity,
                        price=item.product.offer_price,
                    )
                    variant = item.variant
                    variant.variant_stock -= item.quantity
                    variant.save()
                    item.delete()

                if 'applied_coupon' in request.session:
                    del request.session['applied_coupon']

                # wallet 
                if payment_method == 'wallet':
                    wallet = Wallet.objects.get(user=user)
                    if wallet.balance < final_amount:
                        messages.error(request, "Insufficient wallet balance.")
                        return redirect(f'{reverse("cart:checkout")}?cart_items={",".join(cart_item_ids)}&selected_address={selected_address_id}')

                    order.payment_status = True
                    order.order_status = 'Confirmed'
                    order.save()

                    wallet.balance -= final_amount
                    wallet.save()
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=-final_amount,
                        description=f"Payment for order {order.order_id}",
                        transaction_type="Debit"
                    )
                    return redirect('orders:order-confirmation', order_id=order.id)

                # COD 
                if payment_method == 'cash_on_delivery':
                    if final_amount > 5000 :
                        messages.error(request, "Cash on Delivery is not available for orders above ₹5000.")
                        return redirect(f'{reverse("cart:checkout")}?cart_items={",".join(cart_item_ids)}&selected_address={selected_address_id}')

                    order.order_status = 'Confirmed'
                    order.save()
                    return redirect('orders:order-confirmation', order_id=order.id)

                # razorpay 
                if payment_method == 'razorpay':
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    razorpay_order = client.order.create({
                        'amount': int(final_amount * 100),  
                        'currency': 'INR',
                        'payment_capture': '1'
                    })
                    order.payment_id = razorpay_order['id']
                    order.save()
                    return render(request, 'user_side/order/razorpay_payment.html', {
                        'order': order,
                        'razorpay_order_id': razorpay_order['id'],
                        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                        'callback_url': request.build_absolute_uri(reverse('orders:razorpay-callback'))
                    })


        except UserAddress.DoesNotExist:
            messages.error(request, "Selected address does not exist.")
            return HttpResponseRedirect(reverse('cart:checkout'))

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return HttpResponseRedirect(reverse('cart:checkout'))

    else:
        return HttpResponseRedirect(reverse('cart:checkout'))
    


@csrf_exempt
def razorpay_callback(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            order = OrderMain.objects.get(payment_id=razorpay_order_id)
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            client.utility.verify_payment_signature(params_dict)

            order.payment_status = True
            order.order_status = 'Confirmed'
            order.save()

            messages.success(request, "Payment successful and order confirmed!")
            return redirect('orders:order-confirmation', order_id=order.id)
        except OrderMain.DoesNotExist:
            messages.error(request, "Order does not exist.")
            return redirect('orders:order-failure',order_id=order.id)
        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment verification failed.")
            return redirect('orders:order-failure',order_id=order.id)
    else:
        return HttpResponse("Invalid request method.", status=400)


def order_failure(request, order_id):
    print('you fail')
    order = get_object_or_404(OrderMain, id=order_id)
    context = {
        'order': order,
    }
    return render(request, 'user_side/order/order_failure.html', context)    


def order_confirmation(request, order_id):
    order = get_object_or_404(OrderMain, id=order_id)
    future_date_time = timezone.now() + timedelta(days=5)
    estimated_delivery_date = future_date_time.strftime("Arriving By %d %a %B %Y")
    return render(request, 'user_side/order/order_placed.html', {'order': order ,'estimated_delivery_date': estimated_delivery_date})





