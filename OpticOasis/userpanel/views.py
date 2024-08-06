from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserAddress
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from orders.models import OrderMain, OrderSub ,ReturnRequest
from django.views.decorators.http import require_POST
from .models import Wishlist, Product_Variant ,Wallet
from django.http import HttpResponse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserProfileForm ,OrderActionForm
import json

# Create your views here.

@login_required(login_url='/login/')
def user_profile(request):
    return render(request, 'user_side/userpanel/user_profile.html')


@login_required(login_url='/login/')
def add_address(request):
    user_addresses = UserAddress.objects.filter(user=request.user).order_by('-status', 'id')
    context = {
        'user_addresses': user_addresses,
    }

    if request.method == 'POST':
        name = request.POST.get('name')
        house_name = request.POST.get('house_name')
        street_name = request.POST.get('street_name')
        pin_number = request.POST.get('pin_number')
        district = request.POST.get('district')
        state = request.POST.get('state')
        country = request.POST.get('country', 'null')
        phone_number = request.POST.get('phone_number')
        default = request.POST.get('default', 'off') == 'on'
        
        address = UserAddress(
            user=request.user,
            name=name,
            house_name=house_name,
            street_name=street_name,
            pin_number=pin_number,
            district=district,
            state=state,
            country=country,
            phone_number=phone_number,
            status=default
        )
        if default:
            UserAddress.objects.filter(user=request.user, status=True).update(status=False)
        
        address.save()

        

        messages.success(request, 'Address added successfully.')
        return redirect('userpanel:add-address')

    return render(request, 'user_side/userpanel/add_address.html', context)


def user_orders_view(request):
    user = request.user
    orders = OrderMain.objects.filter(user=user).prefetch_related('ordersub_set__variant__product', 'address').order_by('-date')
    return render(request, 'user_side/userpanel/order_list.html', {'orders': orders})


def add_to_wallet(user, description, amount, transaction_type):
    Wallet.objects.create(
        user=user,
        description=description,
        amount=amount,
        transaction_type=transaction_type
    )

def cancel_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(OrderMain, id=order_id, user=request.user)
        reason = request.POST.get('reason')
        order.order_status = 'Canceled'
        order.save()
        # if order.payment_status:
        amount = order.total_amount
        add_to_wallet(request.user, f"Order {order.order_id} canceled: {reason}", amount, 'credit')
        return redirect('userpanel:order-list')
    return HttpResponse(status=405)


def return_order(request, order_id):
    order = get_object_or_404(OrderMain, id=order_id, user=request.user)
    if request.method == "POST":
        reason = request.POST.get("reason")
        # Process the return request
        order.order_status = 'Returned'
        order.save()
        messages.success(request, 'Order has been returned successfully.')
        return redirect('userpanel:order-list')
    return render(request, 'user_side/return_order.html', {'order': order})

def return_item(request, item_id):
    item = get_object_or_404(OrderSub, id=item_id, user=request.user)
    if request.method == "POST":
        reason = request.POST.get("reason")
        # Process the return request
        item.is_active = False
        item.save()
        messages.success(request, 'Item has been returned successfully.')
        return redirect('userpanel:order-list')
    return render(request, 'user_side/return_item.html', {'item': item})


@login_required
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
    user_wallet = Wallet.objects.filter(user=request.user).order_by('-date')
    if not user_wallet.exists():
        Wallet.objects.create(user=request.user, description="Initial wallet creation", amount=0, transaction_type='credit')
        user_wallet = Wallet.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'user_side/userpanel/wallet.html', {'user_wallet': user_wallet})












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