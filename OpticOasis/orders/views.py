from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from datetime import datetime, timedelta
from .models import OrderMain, OrderSub
from cart.models import CartItem, Cart
from userpanel.models import UserAddress
from django.db import transaction
from django.http import JsonResponse
import razorpay
import uuid
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.paginator import Paginator
from utils.decorators import admin_required

# Create your views here.

@admin_required
def admin_order_list(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'Show all')
    items_per_page = request.GET.get('items_per_page', 20)


    orders = OrderMain.objects.all().order_by('-date')
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
def admin_orders_details(request, oid):
    order = get_object_or_404(OrderMain, pk=oid)
    order_items = OrderSub.objects.filter(main_order=order)
    return render(request, 'admin_side/order/order_detail.html', {'orders': order, 'order_sub': order_items})


@admin_required
def change_order_status(request, order_id):
    order = get_object_or_404(OrderMain, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('order_status')
        if order.order_status != 'Canceled':
            order.order_status = new_status
            order.save()
            messages.success(request, 'Order status updated successfully.')
        else:
            messages.error(request, 'Order status cannot be changed as it has been canceled by the user.')
    return redirect('orders:admin-orders-details', oid=order.id)


#user side order fuctions

def generate_unique_order_id():
    return str(uuid.uuid4())


@csrf_exempt
def order_placed(request):
    if request.method == "POST":
        try:
            user = request.user
            cart_item_ids = request.POST.get('cart_item_ids', '')
            selected_address_id = request.POST.get('selected_address')
            payment_method = request.POST.get('payment_method')

            if not cart_item_ids:
                messages.error(request, "Cart is empty.")
                return redirect('cart:checkout')

            cart_item_ids = cart_item_ids.split(',')
            cart_items = CartItem.objects.filter(id__in=cart_item_ids, cart__user=user)
            if not cart_items.exists():
                messages.error(request, "No valid items found. Please try again.")
                return redirect('cart:cart-view')

            for item in cart_items:
                if item.quantity > item.variant.variant_stock:
                    messages.error(request, f"Insufficient stock for {item.product.product_name}.")
                    return redirect('cart:cart-view')
                if not item.product.is_active or not item.variant.variant_status:
                    messages.error(request, f"{item.product.product_name} is no longer available.")
                    return redirect('cart:cart-view')

            address = UserAddress.objects.get(id=selected_address_id)
            total_amount = sum(item.sub_total() for item in cart_items)

            order = OrderMain.objects.create(
                user=user,
                address=address,
                total_amount=total_amount,
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

            if payment_method == 'razorpay':
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                razorpay_order = client.order.create({
                    'amount': int(total_amount * 100),  
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
            else:
                return redirect('orders:order-confirmation', order_id=order.id)
        except UserAddress.DoesNotExist:
            messages.error(request, "Selected address does not exist.")
            return redirect('cart:checkout')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('cart:checkout')
    else:
        return redirect('cart:checkout')

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
    order = get_object_or_404(OrderMain, id=order_id)
    context = {
        'order': order,
    }
    return render(request, 'user_side/order/order_failure.html', context)    

def order_confirmation(request, order_id):
    order = get_object_or_404(OrderMain, id=order_id)
    return render(request, 'user_side/order/order_placed.html', {'order': order})


def add_address(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        name = request.POST.get('name')
        house_name = request.POST.get('house_name')
        street_name = request.POST.get('street_name')
        pin_number = request.POST.get('pin_number')
        district = request.POST.get('district')
        state = request.POST.get('state')
        country = request.POST.get('country', "null")
        phone_number = request.POST.get('phone_number')
        
        try:
            address = UserAddress(
                name=name,
                house_name=house_name,
                street_name=street_name,
                pin_number=pin_number,
                district=district,
                state=state,
                country=country,
                phone_number=phone_number,
                user=request.user
            )
            address.save()
            return JsonResponse({
                'success': True, 
                'address_id': address.id, 
                'name': address.name, 
                'house_name': address.house_name, 
                'street_name': address.street_name, 
                'district': address.district, 
                'state': address.state, 
                'country': address.country, 
                'pin_number': address.pin_number, 
                'phone_number': address.phone_number
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)



