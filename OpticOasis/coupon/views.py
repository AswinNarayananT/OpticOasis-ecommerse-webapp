from django.shortcuts import render ,redirect ,get_object_or_404
from django.contrib import messages
from .forms import CouponForm
from decimal import Decimal
from django.http import JsonResponse
from django.utils import timezone
from .models import Coupon, UserCoupon
from cart.models import Cart, CartItem
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required


# Create your views here.

def list_coupon(request):
    coupons = Coupon.objects.all()
    return render(request, 'admin_side/coupon/list_coupon.html', {'coupons': coupons})


def create_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('coupon:list-coupon') 
    else:
        form = CouponForm()
    return render(request, 'admin_side/coupon/create_edit_coupon.html', {'form': form})


def edit_coupon(request, pk): 
    coupon = get_object_or_404(Coupon, pk=pk)  
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            return redirect('coupon:list-coupon',)
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'admin_side/coupon/create_edit_coupon.html', {'form': form})

def coupon_status(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    
    if request.method == 'POST':
        
        coupon.status = not coupon.status
        coupon.save()
        
        status_message = 'activated' if coupon.status else 'deactivated'
        messages.success(request, f'Coupon successfully {status_message}.')

        return redirect('coupon:list-coupon')
    

# @require_POST
# @login_required
# def apply_coupon(request):
#     coupon_code = request.POST.get('coupon_code')
    
#     if not coupon_code:
#         return JsonResponse({'success': False, 'message': 'Please enter a coupon code.'})

#     try:
#         coupon = Coupon.objects.get(coupon_code=coupon_code, status=True)
#     except Coupon.DoesNotExist:
#         return JsonResponse({'success': False, 'message': 'Invalid coupon code.'})

#     if coupon.expiry_date < timezone.now().date():
#         return JsonResponse({'success': False, 'message': 'This coupon has expired.'})

#     try:
#         cart = Cart.objects.get(user=request.user)
#         cart_items = CartItem.objects.filter(cart=cart, is_active=True)
#         cart_total = sum(item.sub_total() for item in cart_items)
#     except Cart.DoesNotExist:
#         return JsonResponse({'success': False, 'message': 'Your cart is empty.'})

#     if cart_total < coupon.minimum_amount:
#         return JsonResponse({
#             'success': False, 
#             'message': f'Your cart total must be at least ${coupon.minimum_amount} to use this coupon.'
#         })

#     discount_percentage = Decimal(coupon.discount) / Decimal(100)
#     calculated_discount = cart_total * discount_percentage

#     if coupon.maximum_amount:
#         discount_amount = min(calculated_discount, coupon.maximum_amount)
#     else:
#         discount_amount = calculated_discount

#     final_total = cart_total - discount_amount

#     UserCoupon.objects.create(user=request.user, coupon=coupon, used=True, used_at=timezone.now())

#     request.session['applied_coupon'] = coupon.id

#     return JsonResponse({
#         'success': True,
#         'message': 'Coupon applied successfully!',
#         'cart_total': float(cart_total),
#         'discount_amount': float(discount_amount),
#         'final_total': float(final_total)
#     })
@require_POST
@login_required
def apply_coupon(request):
    coupon_code = request.POST.get('coupon_code')
    
    
    if not coupon_code:
        return JsonResponse({'success': False, 'message': 'Please enter a coupon code.'})

    try:
        coupon = Coupon.objects.get(coupon_code=coupon_code, status=True)
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon code.'})

    if coupon.expiry_date < timezone.now().date():
        return JsonResponse({'success': False, 'message': 'This coupon has expired.'})

    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        cart_total = sum(item.sub_total() for item in cart_items)
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Your cart is empty.'})

    if cart_total < coupon.minimum_amount:
        return JsonResponse({
            'success': False, 
            'message': f'Your cart total must be at least ${coupon.minimum_amount} to use this coupon.'
        })

    # Calculate discount amount
    discount_amount = (cart_total * coupon.discount) // 100

    # Apply maximum discount limit
    if coupon.maximum_amount > 0:
        discount_amount = min(discount_amount, coupon.maximum_amount)

    final_total = cart_total - discount_amount

    UserCoupon.objects.create(user=request.user, coupon=coupon, used=True, used_at=timezone.now())

    request.session['applied_coupon'] = coupon.id

    return JsonResponse({
        'success': True,
        'message': 'Coupon applied successfully!',
        'cart_total': float(cart_total),
        'discount_amount': float(discount_amount),
        'final_total': float(final_total)
    })