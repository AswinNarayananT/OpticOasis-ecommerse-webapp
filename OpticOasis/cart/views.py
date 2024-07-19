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

@login_required(login_url='/login/')
def cart_view(request):
    user_cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=user_cart, is_active=True).order_by('-cart__updated_at')
    cart_total = sum(item.sub_total() for item in cart_items)

    for item in cart_items:
        item.variant_image = Product_variant_images.objects.filter(product_variant=item.variant).first()

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
    }
    return render(request, 'user_side/cart/cart_view.html', context)




@login_required(login_url='/login/')
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

        # Validate the new quantity
        if new_quantity < 1 or new_quantity > 5:
            return JsonResponse({'success': False, 'error': 'Quantity must be between 1 and 5'})

        try:
            # Get the cart item for the authenticated user
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            
            # Check if the new quantity exceeds available stock
            if new_quantity > cart_item.variant.variant_stock:
                return JsonResponse({'success': False, 'error': 'Quantity exceeds available stock'})

            # Update the cart item quantity
            cart_item.quantity = new_quantity
            cart_item.save()

            # Recalculate the cart total for the user
            user_cart = cart_item.cart
            cart_items = CartItem.objects.filter(cart=user_cart, is_active=True)
            cart_total = sum(item.sub_total() for item in cart_items)

            response = {
                'success': True,
                'new_total': cart_total,
                'item_sub_total': cart_item.sub_total(),
            }
            return JsonResponse(response)

        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cart item not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})





@login_required
def checkout(request):
    user = request.user
    cart_item_ids = request.GET.get('cart_items', '')  # Get cart item IDs from the GET parameter
    if not cart_item_ids:
        raise ValueError("No cart items selected.")

    cart_item_ids = cart_item_ids.split(',')
    cart_items = CartItem.objects.filter(id__in=cart_item_ids, cart__user=user)

    user_addresses = UserAddress.objects.filter(user=user)

    # Add variant images to each cart item
    for item in cart_items:
        item.variant_image = Product_variant_images.objects.filter(product_variant=item.variant).first()

    # Calculate the total price of the selected items
    cart_total = sum(item.sub_total() for item in cart_items)

    context = {
        'user_addresses': user_addresses,
        'cart_items': cart_items,
        'cart_total': cart_total,
    }
    return render(request, 'user_side/cart/checkout.html', context)

def order_placed_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_placed.html', {'order': order})




