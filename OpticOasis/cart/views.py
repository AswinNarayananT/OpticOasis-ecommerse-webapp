from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem
from product.models import Products, Product_Variant ,Product_variant_images
from django.http import JsonResponse
from django.contrib import messages
from django.http import JsonResponse
from userpanel.models import UserAddress
from cart.models import CartItem


# Create your views here.

def cart_view(request):
    user_cart = Cart.objects.get(user=request.user)
    cart_items = CartItem.objects.filter(cart=user_cart, is_active=True).order_by('-cart__updated_at')
    cart_total = sum(item.sub_total() for item in cart_items)

    for item in cart_items:
        item.variant_image = Product_variant_images.objects.filter(product_variant=item.variant).first()

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
    }
    return render(request, 'user_side/cart_view.html', context)





def add_to_cart(request):
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))  
        variant = get_object_or_404(Product_Variant, id=variant_id)
        product = variant.product

        cart, created = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'fail'})

def remove_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart:cart-view') 


def update_cart_quantity(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        new_quantity = int(request.POST.get('quantity'))

        # Ensure quantity is between 1 and 5
        if new_quantity < 1 or new_quantity > 5:
            return JsonResponse({'success': False, 'error': 'Quantity must be between 1 and 5'})

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            
            # Check if the new quantity exceeds the stock
            if new_quantity > cart_item.variant.variant_stock:
                return JsonResponse({'success': False, 'error': 'Quantity exceeds available stock'})

            cart_item.quantity = new_quantity
            cart_item.save()

            # Recalculate totals
            user_cart = cart_item.cart
            cart_total = sum(item.sub_total() for item in CartItem.objects.filter(cart=user_cart, is_active=True))

            response = {
                'success': True,
                'new_total': cart_total,
                'item_sub_total': cart_item.sub_total(),
            }
            return JsonResponse(response)

        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cart item not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})






@login_required
def checkout(request):
    user = request.user
    # cart_items = CartItem.objects.filter(user=user)
    # cart_total = sum(item.sub_total for item in cart_items)
    user_addresses = UserAddress.objects.filter(user=user)

    # if request.method == 'POST':
    #     selected_address_id = request.POST.get('selected_address')
    #     payment_method = request.POST.get('payment_method')

    #     if selected_address_id == 'new':
    #         # Create new address
    #         new_address = UserAddress(
    #             user=user,
    #             name=request.POST.get('name'),
    #             house_name=request.POST.get('house_name'),
    #             street_name=request.POST.get('street_name'),
    #             pin_number=request.POST.get('pin_number'),
    #             district=request.POST.get('district'),
    #             state=request.POST.get('state'),
    #             country=request.POST.get('country'),
    #             phone_number=request.POST.get('phone_number')
    #         )
    #         new_address.save()
    #         selected_address = new_address
        # else:
        #     selected_address = UserAddress.objects.get(id=selected_address_id)

        # # Create order
        # order = Order.objects.create(
        #     user=user,
        #     address=selected_address,
        #     total_amount=cart_total,
        #     payment_method=payment_method
        # )

        # # Create order items
        # for cart_item in cart_items:
        #     OrderItem.objects.create(
        #         order=order,
        #         product=cart_item.product,
        #         quantity=cart_item.quantity,
        #         price=cart_item.product.price
        #     )

        # Clear the cart
        # cart_items.delete()

        # return redirect('order_confirmation', order_id=order.id)

    context = {
        'user_addresses': user_addresses,
        # 'cart_items': cart_items,
        # 'cart_total': cart_total,
    }
    return render(request, 'user_side/cart/checkout.html',context)