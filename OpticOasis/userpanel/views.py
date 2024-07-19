from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserAddress
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