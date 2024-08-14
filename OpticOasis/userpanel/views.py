from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserAddress ,Wallet ,WalletTransaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from orders.models import OrderMain, OrderSub ,ReturnRequest
from django.views.decorators.http import require_POST
from .models import Wishlist, Product_Variant ,Wallet
from django.http import HttpResponse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserProfileForm ,UserAddressForm
import json
from django.utils import timezone
from decimal import Decimal
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.http import HttpResponse, FileResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch



# Create your views here.

@login_required(login_url='/login/')
def user_profile(request):
    return render(request, 'user_side/userpanel/user_profile.html')


@login_required(login_url='/login/')
def user_address(request):
    user_addresses = UserAddress.objects.filter(user=request.user).order_by('-status', 'id')
    paginator = Paginator(user_addresses, 2)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }

    return render(request, 'user_side/userpanel/user_address.html', context)


def add_or_edit_address(request, address_id=None):
    if address_id:
        address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    else:
        address = None

    if request.method == 'POST':
        form = UserAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            return redirect('userpanel:user-address')
    else:
        form = UserAddressForm(instance=address)

    context = {
        'form': form,
        'is_edit': address_id is not None,
        'address_id': address_id
    }
    return render(request, 'user_side/userpanel/add_address.html', context)

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    address.delete()
    messages.success(request, 'Address deleted successfully.')
    return redirect('userpanel:user-address')


def user_orders_view(request):
    user = request.user
    orders = OrderMain.objects.filter(user=user).prefetch_related('ordersub_set__variant__product', 'address').order_by('-id')
    status_list = ["Pending", "Awaiting payment", "Confirmed", "Shipped"]

    paginator = Paginator(orders, 3)  
    page = request.GET.get('page')

    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:

        orders_page = paginator.page(1)
    except EmptyPage:
        orders_page = paginator.page(paginator.num_pages)

    for order in orders_page:
        order.has_active_items = order.ordersub_set.filter(is_active=True).exists()
        print(f"Order ID: {order.id}, Status: {order.order_status}, Has Active Items: {order.has_active_items}")
        for item in order.ordersub_set.all():
            item.return_status = ReturnRequest.objects.filter(order_sub=item).first()

    return render(request, 'user_side/userpanel/order_list.html', {'orders': orders_page, 'status_list': status_list})



@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(OrderMain, id=order_id, user=request.user)

    if order.order_status not in ['Pending', 'Confirmed', 'Shipped']:
        messages.error(request, 'Order cannot be canceled at this stage.')
        return redirect('userpanel:order-list')

    with transaction.atomic():
        refund_amount = Decimal('0.00')
        active_items = order.ordersub_set.filter(is_active=True)

        for item in active_items:
            item_total_cost = Decimal(str(item.total_cost()))
            order_total_amount = Decimal(str(order.total_amount))
            order_discount_amount = Decimal(str(order.discount_amount))

            item_discount_amount = (order_discount_amount * item_total_cost) / order_total_amount
            item_refund_amount = item_total_cost - item_discount_amount

            refund_amount += item_refund_amount
            item.is_active = False
            item.save()

        order.order_status = 'Canceled'
        order.is_active = False
        order.save()

        if refund_amount > 0:
            if order.payment_option == 'razorpay' or order.payment_option == 'wallet':
                wallet, _ = Wallet.objects.get_or_create(user=request.user)
                wallet.balance += refund_amount
                wallet.updated_at = timezone.now()
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=float(refund_amount),
                    description=f"Refund for canceled order {order.order_id}",
                    transaction_type='credit'
                )
                messages.success(request, f'Order {order.order_id} has been canceled')
        else:
            messages.success(request, f'Order {order.order_id} has been canceled successfully.')

    return redirect('userpanel:order-list')


@login_required
@require_POST
def cancel_order_item(request):
    order_sub_id = request.POST.get('order_sub_id')
    order_item = get_object_or_404(OrderSub, id=order_sub_id, user=request.user)
    main_order = order_item.main_order

    if not order_item.is_active:
        messages.error(request, 'Order item is already canceled.')
        return redirect('userpanel:order-list')

    if main_order.order_status not in ['Pending', 'Confirmed', 'Shipped']:
        messages.error(request, 'Order cannot be canceled at this stage.')
        return redirect('userpanel:order-list')
    
    if main_order.payment_option == 'razorpay' or main_order.payment_option == 'wallet':
        
        item_total_cost = Decimal(str(order_item.total_cost()))
        order_total_amount = Decimal(str(main_order.total_amount))
        order_discount_amount = Decimal(str(main_order.discount_amount))

        item_discount_amount = (order_discount_amount * item_total_cost) / order_total_amount
        refund_amount = item_total_cost - item_discount_amount

        wallet, created = Wallet.objects.get_or_create(user=request.user)
        wallet.balance = float(Decimal(str(wallet.balance)) + refund_amount)
        wallet.updated_at = timezone.now()
        wallet.save()

        WalletTransaction.objects.create(
            wallet=wallet,
            amount=float(refund_amount),
            description=f'Refund for canceled item {order_item.variant.product.product_name}',
            transaction_type='credit'
        )

    order_item.is_active = False
    order_item.status='Canceled'
    order_item.save()

    all_canceled = not main_order.ordersub_set.filter(is_active=True).exists()
    
    if all_canceled:
        main_order.order_status = 'Canceled'
        main_order.save()

    messages.success(request, 'Order item canceled successfully.')
    return redirect('userpanel:order-list')


def return_order(request, order_id):
    order = get_object_or_404(OrderMain, id=order_id, user=request.user)

    if order.order_status == 'Returned':
        messages.error(request, 'This order has already been returned.')
        return redirect('userpanel:order-list')
    
    if request.method == "POST":
        reason = request.POST.get("reason")
        ReturnRequest.objects.create(
            order_main=order,
            reason=reason
        )
        order.order_status = 'Returned'
        order.save()
        messages.success(request, 'Return request has been submitted successfully.')
        return redirect('userpanel:order-list')
    return render(request, 'user_side/return_order.html', {'order': order})


def return_item(request, item_id):
    item = get_object_or_404(OrderSub, id=item_id, user=request.user)

    if not item.is_active:
        messages.error(request, 'This item has already been returned.')
        return redirect('userpanel:order-list')
    
    if request.method == "POST":
        reason = request.POST.get("reason")
        ReturnRequest.objects.create(
            order_main=item.main_order,
            order_sub=item,
            reason=reason
        )
        item.is_active = False
        item.status='Return requested'
        item.save()

        all_returned = not item.main_order.ordersub_set.filter(is_active=True).exists()
        
        if all_returned:
            item.main_order.order_status = 'Returned'
            item.main_order.save()

        messages.success(request, 'Return request for the item has been submitted successfully.')
        return redirect('userpanel:order-list')
    return render(request, 'user_side/return_item.html', {'item': item})


@login_required(login_url='/login/')
def wishlist(request):
    wishlists = Wishlist.objects.filter(user=request.user)
    return render(request, 'user_side/userpanel/wishlist.html', {'wishlists': wishlists})


@login_required
@require_POST
def toggle_wishlist(request):
    try:
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        
        if not variant_id:
            return JsonResponse({'status': 'error', 'message': 'No variant ID provided'}, status=400)
        
        variant = Product_Variant.objects.get(id=variant_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, variant=variant)
        
        if not created:
            wishlist_item.delete()
            return JsonResponse({'status': 'removed'})
        else:
            return JsonResponse({'status': 'added'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Product_Variant.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Variant not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    

@login_required(login_url='/login/')
def remove_from_wishlist(request):
    if request.method == 'POST':
        wishlist_id = request.POST.get('wishlist_id')
        wishlist_item = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
        wishlist_item.delete()

        return redirect('userpanel:wishlist') 
    else:
        return redirect('userpanel:wishlist')  
    

def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been successfully updated.')
            return redirect('userpanel:user-profile') 
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'user_side/userpanel/password_change_form.html', {'form': form})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(instance=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('userpanel:user-profile') 
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'user_side/userpanel/edit_profile.html', {'form': form})


@login_required
def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)

    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-timestamp')

    paginator = Paginator(transactions, 6)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    context = {
        'wallet': wallet,
        'transactions': page_obj, 
    }

    return render(request, 'user_side/userpanel/wallet.html', context)




@login_required
def download_invoice(request, order_id):
    try:
        order_main = get_object_or_404(OrderMain, id=order_id)
        order_sub = OrderSub.objects.filter(main_order=order_main)
        buffer = BytesIO()

        try:
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            subtitle_style = ParagraphStyle(name="Subtitle", fontSize=14, leading=18, spaceAfter=12)
            normal_style = styles['Normal']

            elements.append(Paragraph("OPTIC OASIS", title_style))
            elements.append(Paragraph("INVOICE", subtitle_style))
            elements.append(Spacer(1, 0.5 * inch))

            elements.append(Paragraph(f"<b>Order Number:</b> {order_main.order_id}", normal_style))
            elements.append(Paragraph(f"<b>Order Date:</b> {order_main.date.strftime('%B %d, %Y')}", normal_style))
            elements.append(Paragraph(f"<b>Customer Name:</b> {order_main.address.name}", normal_style))
            elements.append(Paragraph(f"<b>Email:</b> {order_main.user.email}", normal_style))
            elements.append(Paragraph(f"<b>Phone:</b> {order_main.address.phone_number}", normal_style))
            elements.append(Paragraph(f"<b>Address:</b> {order_main.address.house_name}, {order_main.address.street_name}, {order_main.address.district}, {order_main.address.state}, {order_main.address.pin_number}, {order_main.address.country}", normal_style))
            elements.append(Spacer(1, 0.5 * inch))

            data = [['Product', 'Quantity', 'Unit Price', 'Total Price']]
            for item in order_sub:
                data.append([
                    item.variant.product.product_name,
                    str(item.quantity),
                    f" {item.price:.2f}",
                    f" {item.price * item.quantity:.2f}"
                ])

            data.append(['', '', 'Subtotal:', f" {order_main.total_amount:.2f}"])
            data.append(['', '', 'Discount:', f" {order_main.discount_amount:.2f}"])
            data.append(['', '', 'Shipping:', 'Free'])
            data.append(['', '', 'Total:', f" {order_main.final_amount:.2f}"])

            table = Table(data, colWidths=[2.5 * inch, 1.25 * inch, 1.25 * inch, 1.5 * inch])
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (2, -4), (-1, -2), colors.lightgrey),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
            ])
            table.setStyle(style)
            elements.append(table)

            # Footer Note
            elements.append(Spacer(1, 1 * inch))
            elements.append(Paragraph("Thank you for shopping with OPTIC OASIS!", normal_style))

            doc.build(elements)
        except Exception as e:
            return HttpResponse(f'Error generating PDF content: {str(e)}', status=500)

        buffer.seek(0)
        
        return FileResponse(buffer, as_attachment=True, filename=f'invoice_{order_id}.pdf')

    except Exception as e:
        return HttpResponse(f'Error generating PDF: {str(e)}', status=500)


















# @login_required(login_url='/login/')
# def add_address(request):
#     user_addresses = UserAddress.objects.filter(user=request.user).order_by('-status', 'id')
#     context = {
#         'user_addresses': user_addresses,
#     }

#     if request.method == 'POST':
#         name = request.POST.get('name')
#         house_name = request.POST.get('house_name')
#         street_name = request.POST.get('street_name')
#         pin_number = request.POST.get('pin_number')
#         district = request.POST.get('district')
#         state = request.POST.get('state')
#         country = request.POST.get('country', 'null')
#         phone_number = request.POST.get('phone_number')
#         default = request.POST.get('default', 'off') == 'on'
        

#         address = UserAddress(
#             user=request.user,
#             name=name,
#             house_name=house_name,
#             street_name=street_name,
#             pin_number=pin_number,
#             district=district,
#             state=state,
#             country=country,
#             phone_number=phone_number,
#             status=default
#         )
#         if default:
#             UserAddress.objects.filter(user=request.user, status=True).update(status=False)
        
#         address.save()
#         messages.success(request, 'Address added successfully.')
#         return redirect('userpanel:add-address')  
    
#     return render(request, 'user_side/userpanel/add_address.html', context)