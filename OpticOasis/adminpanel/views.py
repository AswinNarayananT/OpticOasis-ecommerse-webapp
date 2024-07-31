from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login ,logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.models import User
from accounts.forms import UserRegistrationForm  
from accounts.models import User  
from utils.decorators import admin_required
from datetime import datetime
from orders.models import OrderMain
# from django.views.decorators.csrf import csrf_protect

# Create your views here.

def admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.is_admin:
                login(request, user)
                return redirect('admin_dashboard') 
            else:
                messages.error(request, 'You are not authorized to access this page.')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'admin_side/admin/admin_login.html')


@admin_required
def admin_dashboard(request):
    orders = OrderMain.objects.filter(order_status="Delivered")
    return render(request, 'admin_side/admin/admin_dashboard.html', {'orders': orders})


def sales_report(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return redirect('admin_panel:sales-report')
            
            orders = OrderMain.objects.filter(date__range=[start_date, end_date], order_status="Delivered")
            return render(request, 'admin_side/dashboard/salesreport.html', {'orders': orders})
    
    orders = OrderMain.objects.filter(order_status="Delivered")
    return render(request, 'admin_side/admin/salesreport.html', {'orders': orders})


@admin_required
def user_list(request):
    users = User.objects.filter(is_admin=False)
    return render(request, 'admin_side/user/user_view.html', {'users': users})


@admin_required
def user_create(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  
            user.save()
            messages.success(request, 'User created successfully.')
            return redirect('user_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'admin_side/user/user_form.html', {'form': form})


@admin_required
def user_block(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_blocked = True
    user.save()
    messages.success(request, 'User blocked successfully.')
    return redirect('user_list')


@admin_required
def user_unblock(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_blocked = False
    user.save()
    messages.success(request, 'User unblocked successfully.')
    return redirect('user_list')


@admin_required
def user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False   
    user.save()
    messages.success(request, 'User deleted successfully.')
    return redirect('user_list')


@admin_required
def user_undelete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True   
    user.save()
    messages.success(request, 'User deleted successfully.')
    return redirect('user_list')

@admin_required
def admin_logout(request):
    logout(request)
    return redirect('admin_login')


