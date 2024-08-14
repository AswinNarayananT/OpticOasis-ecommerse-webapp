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
from orders.models import OrderMain ,OrderSub
from django.db.models import Sum
from django.utils.timezone import now
from django.utils.timezone import now, timedelta
from product.models import Products , Product_Variant , Product_variant_images
from django.db.models import Sum, Count
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Sum, Count, F, Q
from brand.models import Brand
from category.models import Category

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
    delivered_orders = OrderMain.objects.filter(order_status='Delivered')

    total_order_amount = delivered_orders.aggregate(Sum('final_amount'))['final_amount__sum'] or 0
    total_order_count = delivered_orders.count()

    current_month = now().month
    current_year = now().year

    monthly_orders = OrderMain.objects.filter(date__year=current_year, date__month=current_month)
    monthly_earnings = monthly_orders.aggregate(Sum('final_amount'))['final_amount__sum'] or 0
    total_discounts_given = monthly_orders.aggregate(Sum('discount_amount'))['discount_amount__sum'] or 0

    last_7_days = [now().date() - timedelta(days=i) for i in range(7)][::-1]
    sales_data = []
    for day in last_7_days:
        day_sales = OrderMain.objects.filter(order_status='Delivered', date=day).aggregate(Sum('final_amount'))['final_amount__sum'] or 0
        sales_data.append(day_sales)

     # Best selling calculations
    best_selling_product = Products.objects.filter(
        product_variant__ordersub__main_order__order_status='Delivered'
    ).annotate(
        sales_count=Count('product_variant__ordersub')
    ).order_by('-sales_count').first()

    best_selling_category = Category.objects.filter(
        products__product_variant__ordersub__main_order__order_status='Delivered'
    ).annotate(
        sales_count=Count('products__product_variant__ordersub')
    ).order_by('-sales_count').first()

    best_selling_brand = Brand.objects.filter(
        products__product_variant__ordersub__main_order__order_status='Delivered'
    ).annotate(
        sales_count=Count('products__product_variant__ordersub')
    ).order_by('-sales_count').first()
    
    context = {
        'total_order_amount': total_order_amount,
        'total_order_count': total_order_count,
        'monthly_earnings': monthly_earnings,
        'total_discounts_given': total_discounts_given,
        'sales_data': sales_data,
        'days': [day.strftime("%A") for day in last_7_days],
        'best_selling_category': best_selling_category,
        'best_selling_brand': best_selling_brand,
        'best_selling_product': best_selling_product,
    }
    
    return render(request, 'admin_side/admin/admin_dashboard.html', context)



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


