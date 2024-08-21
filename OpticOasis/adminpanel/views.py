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
from django.utils import timezone
from django.utils.timezone import now, timedelta
from product.models import Products , Product_Variant , Product_variant_images
from django.db.models import Sum, Count
from datetime import timedelta
from django.contrib import messages
from django.db.models import Sum, Count, F, Q
from brand.models import Brand
from category.models import Category
import json
from django.db.models.functions import ExtractMonth, ExtractYear, TruncMonth

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
    monthly_orders = OrderMain.objects.filter(date__year=current_year, date__month=current_month,order_status='Delivered')
    monthly_earnings = monthly_orders.aggregate(Sum('final_amount'))['final_amount__sum'] or 0
    total_discounts_given = monthly_orders.aggregate(Sum('discount_amount'))['discount_amount__sum'] or 0


    monthly_order_count = OrderMain.objects.filter(
        order_status="Delivered"
    ).annotate(
        month=ExtractMonth('date'),
        year=ExtractYear('date')
    ).values('year', 'month').annotate(count=Count('id')).order_by('year', 'month')

    labels = [f'{entry["month"]}/{entry["year"]}' for entry in monthly_order_count]
    data = [entry['count'] for entry in monthly_order_count]

    user_registrations = User.objects.annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(count=Count('id')).order_by('month')

    user_labels = [entry['month'].strftime('%b %Y') for entry in user_registrations]
    user_data = [entry['count'] for entry in user_registrations]
    
    context = {
        'total_order_amount': total_order_amount,
        'total_order_count': total_order_count,
        'monthly_earnings': monthly_earnings,
        'total_discounts_given': total_discounts_given,
        'labels': json.dumps(labels),
        'data': json.dumps(data),
        'user_labels': json.dumps(user_labels),
        'user_data': json.dumps(user_data)
    }
    
    return render(request, 'admin_side/admin/admin_dashboard.html', context)

def best_selling_products(request):
    best_selling_products = OrderSub.objects.filter(
        main_order__order_status="Delivered"
    ).values(
        'variant__product__id',
        'variant__product__product_name'
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')
    
    top_product = best_selling_products.first()
    
    return render(request, 'admin_side/admin/best_products.html', {
        'top_product': top_product,
        'best_selling_products': best_selling_products
    })



def best_selling_categories(request):
    category_sales = OrderSub.objects.filter(
        main_order__order_status="Delivered"
    ).values(
        'variant__product__product_category__id',
        'variant__product__product_category__category_name',
        'variant__product__thumbnail',
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')

    seen_categories = set()
    distinct_categories = []
    for category in category_sales:
        if category['variant__product__product_category__id'] not in seen_categories:
            distinct_categories.append(category)
            seen_categories.add(category['variant__product__product_category__id'])

    top_category = distinct_categories[0] if distinct_categories else None
    
    return render(request, 'admin_side/admin/best_categories.html', {
        'top_category': top_category,
        'best_selling_categories': distinct_categories,
    })

def best_selling_brands(request):
    best_selling_brands = OrderSub.objects.filter(
        main_order__order_status="Delivered"
    ).values(
        'variant__product__product_brand__id',
        'variant__product__product_brand__brand_name',
        'variant__product__product_brand__brand_image'  
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')

    top_brand = best_selling_brands.first()

    return render(request, 'admin_side/admin/best_brands.html', {
        'top_brand': top_brand,
        'best_selling_brands': best_selling_brands,
    })

def sales_report(request):
    filter_type = request.GET.get('filter', None)
    now = timezone.now()
    start_date = end_date = None 

    if filter_type == 'weekly':
        start_date = now - timedelta(days=now.weekday())
        end_date = now
    elif filter_type == 'monthly':
        start_date = now.replace(day=1)
        end_date = now

    if start_date and end_date:
        orders = OrderMain.objects.filter(
            order_status="Delivered",
            is_active=True,
            date__range=[start_date, end_date]
        )
    else:
        orders = OrderMain.objects.filter(
            order_status="Delivered",
            is_active=True
        )

    total_discount = orders.aggregate(total=Sum('discount_amount'))['total'] or 0
    total_orders = orders.aggregate(total=Count('id'))['total'] or 0
    total_order_amount = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    return render(request, 'admin_side/admin/salesreport.html', {
        'orders': orders,
        'total_discount': total_discount,
        'total_orders': total_orders,
        'total_order_amount': total_order_amount
    })

def order_date_filter(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return redirect('sales-report')

            orders = OrderMain.objects.filter(date__range=[start_date, end_date], order_status="Order Placed")
            total_discount = orders.aggregate(total=Sum('discount_amount'))['total'] or 0
            total_orders = orders.aggregate(total=Count('id'))['total'] or 0
            total_order_amount = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

            return render(request, 'admin_side/admin/salesreport.html', {
                'orders': orders,
                'total_discount': total_discount,
                'total_orders': total_orders,
                'total_order_amount': total_order_amount,
            })

    return redirect('sales-report')


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


