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
import uuid

# Create your views here.

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
            
            total_amount = sum(CartItem.objects.get(id=item_id).sub_total() for item_id in cart_item_ids)
            
            order = OrderMain.objects.create(
                user=user,
                address=address,
                total_amount=total_amount,
                payment_option=payment_method,
                order_id=generate_unique_order_id(), 
                payment_status=False,  
            )

            
            for item_id in cart_item_ids:
                cart_item = CartItem.objects.get(id=item_id)
                OrderSub.objects.create(
                    user=user,
                    main_order=order,
                    variant=cart_item.variant,
                    quantity=cart_item.quantity,
                )
                item.variant.variant_stock -= item.quantity
                item.variant.save()
                item.delete()

            
            request.session['cart'] = []

            return redirect('orders:order-confirmation', order_id=order.id)
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('cart:checkout')
    else:
        return redirect('cart:checkout')

    



def order_confirmation(request, order_id):
    order = get_object_or_404(OrderMain, id=order_id)
    return render(request, 'user_side/cart/order_placed.html', {'order': order})



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



# @login_required
# def order_placed(request):
#     if request.method == 'POST':
#         current_user = request.user
#         cart_item_ids = request.POST.get('cart_item_ids', '').split(',')
#         print(cart_item_ids)
#         cart_items = CartItem.objects.filter(id__in=cart_item_ids, cart__user=current_user)

#         if not cart_items.exists():
#             messages.error(request, 'No items in cart')
#             return redirect('cart:checkout')

#         address_id = request.POST.get('selected_address')
#         try:
#             address = UserAddress.objects.get(id=address_id, user=current_user)
#         except UserAddress.DoesNotExist:
#             messages.error(request, 'Invalid address selected')
#             return redirect('cart:checkout')

#         payment_option = request.POST.get('payment_method')

#         if not payment_option:
#             messages.error(request, 'Select Payment Option')
#             return redirect('cart:checkout')

#         # Validate cart items
#         for cart_item in cart_items:
#             if not cart_item.variant.variant_status:
#                 messages.error(request, f'Select variant for {cart_item.product.product_name}')
#                 return redirect('cart:checkout')

#             if cart_item.variant.variant_stock < cart_item.quantity:
#                 messages.error(request, f'{cart_item.product.product_name} is out of stock')
#                 return redirect('cart:checkout')

#             if not cart_item.product.is_active:
#                 messages.error(request, f'{cart_item.product.product_name} is currently inactive')
#                 return redirect('cart:checkout')

#         try:
#             with transaction.atomic():
#                 # Generate order ID and payment ID
#                 current_date_time = datetime.now()
#                 formatted_date_time = current_date_time.strftime("%H%m%S%Y")
#                 unique = get_random_string(length=4, allowed_chars='1234567890')
#                 order_id = f"{current_user.id}{formatted_date_time}{unique}"

#                 formatted_date_time = current_date_time.strftime("%m%Y%H%S")
#                 unique = get_random_string(length=2, allowed_chars='1234567890')
#                 payment_id = f"{unique}{current_user.id}{formatted_date_time}"

#                 # Create main order
#                 order_main = OrderMain.objects.create(
#                     user=current_user,
#                     address=address,
#                     total_amount=sum(item.sub_total() for item in cart_items),
#                     payment_option=payment_option,
#                     order_id=order_id,
#                     payment_id=payment_id
#                 )

#                 # Create order sub items and update stock
#                 for cart_item in cart_items:
#                     OrderSub.objects.create(
#                         user=current_user,
#                         main_order=order_main,
#                         variant=cart_item.variant,
#                         quantity=cart_item.quantity,
#                     )

#                     variant = cart_item.variant
#                     variant.variant_stock -= cart_item.quantity
#                     variant.save()

#                 # Clear the cart
#                 cart_items.delete()

#                 # Calculate estimated delivery date
#                 current_date_time = datetime.now()
#                 future_date_time = current_date_time + timedelta(days=5)
#                 formatted_future_date = future_date_time.strftime("Arriving By %a, %b %d %Y")

#                 messages.success(request, 'Order placed successfully!')
#                 return render(request, 'user_side/cart/order_placed.html', {
#                     'main_order': order_main,
#                     'formatted_future_date': formatted_future_date
#                 })

#         except Exception as e:
#             messages.error(request, f'An error occurred while placing your order: {str(e)}')
#             return redirect('cart:checkout')

#     else:
#         return redirect('cart:checkout')

