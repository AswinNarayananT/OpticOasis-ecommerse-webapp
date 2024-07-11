from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem
from product.models import Products, Product_Variant ,Product_variant_images
from django.http import JsonResponse
from django.contrib import messages


# Create your views here.


def cart_view(request):
    user_cart = Cart.objects.get(user=request.user)
    cart_items = CartItem.objects.filter(cart=user_cart)

    for item in cart_items:
        item.variant_image = Product_variant_images.objects.filter(product_variant=item.variant).first()

    context = {
        'cart_items': cart_items
    }
    return render(request, 'user_side/cart_view.html', context)


def add_to_cart(request):
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))  # Default quantity is 1
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

