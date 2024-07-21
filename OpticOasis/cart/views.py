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


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def update_cart_quantity(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        new_quantity = request.POST.get('quantity')

        if not item_id or not new_quantity:
            return JsonResponse({'success': False, 'error': 'Missing item ID or quantity'})

        try:
            new_quantity = int(new_quantity)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid quantity'})

        if new_quantity < 1 or new_quantity > 5:
            return JsonResponse({'success': False, 'error': 'Quantity must be between 1 and 5'})

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)

            if new_quantity > cart_item.variant.variant_stock:
                return JsonResponse({'success': False, 'error': 'Quantity exceeds available stock'})

            cart_item.quantity = new_quantity
            cart_item.save()

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
    cart_item_ids = request.GET.get('cart_items', '')
    
    if not cart_item_ids:
        messages.error(request, "No items selected.Please select items before proceeding to checkout.")
        return redirect('cart:cart-view') 
    

    cart_item_ids = cart_item_ids.split(',')
    cart_items = CartItem.objects.filter(id__in=cart_item_ids, cart__user=user)
    if not cart_items.exists():
        messages.error(request, "No valid items found in cart. Please try again.")
        return redirect('cart:cart-view')  
    
    for item in cart_items:
        if item.quantity > item.variant.variant_stock:
            messages.error(request, f"Insufficient stock for {item.product.product_name}.")
            return redirect('cart:cart-view')
        if not item.product.is_active or not item.variant.variant_status:
            messages.error(request, f"{item.product.product_name} is no longer available.")
            return redirect('cart:cart-view')

    user_addresses = UserAddress.objects.filter(user=user)
    

    for item in cart_items:
        item.variant_image = Product_variant_images.objects.filter(product_variant=item.variant).first()

    cart_total = sum(item.sub_total() for item in cart_items)

    context = {
        'user_addresses': user_addresses,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_item_ids': ','.join(map(str, cart_items.values_list('id', flat=True))),
    }
    return render(request, 'user_side/cart/checkout.html', context)



@login_required
def check_cart_status(request):
    variant_id = request.GET.get('variant_id')
    user = request.user
    
    # Get the user's cart. If no cart exists, it creates a new one.
    cart, created = Cart.objects.get_or_create(user=user)
    
    # Check if the specified variant is in the cart
    is_in_cart = CartItem.objects.filter(cart=cart, variant_id=variant_id, is_active=True).exists()
    
    return JsonResponse({'is_in_cart': is_in_cart})










