from django.shortcuts import render,redirect,get_object_or_404
from .models import Products, Category, Brand ,Product_images ,Product_Variant,Product_variant_images 
from utils.decorators import admin_required
from django.http import HttpResponse
from django.utils import timezone
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Products, Review
from django.db.models import Avg, Count, Sum, Prefetch
from django.db.models.functions import Lower
from django.http import JsonResponse
from django.template.loader import render_to_string
from userpanel.models import Wishlist



# Create your views here.


@admin_required
def list_product(request):
    products = Products.objects.all().order_by('-created_at') 
    return render(request, 'admin_side/product/list_product.html', {'products': products})

def product_detail(request, product_id):
    products = get_object_or_404(Products, id=product_id) 
    images = Product_images.objects.filter(product=products)
    return render(request, 'admin_side/product/product_detail.html', {'products': products, 'images': images})

@admin_required
def create_product(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        product_description = request.POST.get('product_description')
        product_category_id = request.POST.get('product_category')
        product_brand_id = request.POST.get('product_brand')
        price = request.POST.get('price')
        offer_price = request.POST.get('offer_price')
        is_active = request.POST.get('is_active') == 'on'
        thumbnail = request.FILES.get('thumbnail')

        product_category = Category.objects.get(id=product_category_id) if product_category_id else None
        product_brand = Brand.objects.get(id=product_brand_id) if product_brand_id else None

        product = Products(
            product_name=product_name,
            product_description=product_description,
            product_category=product_category,
            product_brand=product_brand,
            price=price,
            offer_price=offer_price,
            thumbnail=thumbnail,
            is_active=is_active,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
        product.save()

        return redirect('product:list-product')

    categories = Category.objects.all()
    brands = Brand.objects.all()
    return render(request, 'admin_side/product/create_product.html', {'categories': categories, 'brands': brands})

@admin_required
def edit_product(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    if request.method == 'POST':
        product.product_name = request.POST.get('product_name')
        product.product_description = request.POST.get('product_description')
        product_category_id = request.POST.get('product_category')
        product_brand_id = request.POST.get('product_brand')
        product.price = request.POST.get('price')
        product.offer_price = request.POST.get('offer_price')

        if request.FILES.get('thumbnail'):
            product.thumbnail = request.FILES.get('thumbnail')
        product.is_active = request.POST.get('is_active') == 'on'

        product.product_category = Category.objects.get(id=product_category_id) if product_category_id else None
        product.product_brand = Brand.objects.get(id=product_brand_id) if product_brand_id else None

        product.updated_at = timezone.now()  # Update the updated_at timestamp
        product.save()
        return redirect('product:product-detail', product_id=product_id)

    categories = Category.objects.all()
    brands = Brand.objects.all()
    return render(request, 'admin_side/product/edit_product.html', {'product': product, 'categories': categories, 'brands': brands})


@admin_required
def product_status(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    product.is_active = not product.is_active
    product.save()
    return redirect('product:product-detail',product_id=product_id)

@admin_required
def add_images(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    if request.method == 'POST':
        thumbnail = request.FILES.get('thumbnail')
        images = request.FILES.getlist('images')
        
        if thumbnail:
            product.thumbnail = thumbnail
            product.save()

        for image in images:
            Product_images.objects.create(product=product, images=image)

        return redirect('product:product-detail',product_id=product_id)

    return render(request, 'admin_side/product/add_images.html', {'product': product})


@admin_required
def add_variant(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    variants = Product_Variant.objects.filter(product=product)
    
    if request.method == 'POST':
        size = request.POST.get('size')
        colour_name = request.POST.get('colour_name')
        variant_stock = request.POST.get('variant_stock')
        variant_status = request.POST.get('variant_status') == 'on'
        colour_code = request.POST.get('colour_code')

        if Product_Variant.objects.filter(product=product, colour_name=colour_name, colour_code=colour_code).exists():
            messages.error(request, "A variant with this color name and color code already exists.")
            return redirect('product:add-variant', product_id=product_id)
        
        variant = Product_Variant.objects.create(
            product=product,
            size=size,
            colour_name=colour_name,
            variant_stock=variant_stock,
            variant_status=variant_status,
            colour_code=colour_code
        )

        return redirect('product:add-variant-image', product_variant_id=variant.id)  

    return render(request, 'admin_side/variant/add_variant.html', {'product': product, 'variants': variants})


def add_variant_image(request, product_variant_id):
    product_variant = get_object_or_404(Product_Variant, id=product_variant_id)
    
    if request.method == 'POST':
        images = request.FILES.getlist('images')
        
        if images:
            for image in images:
                Product_variant_images.objects.create(product_variant=product_variant, images=image)
            return redirect('product:variant-detail', product_id=product_variant.product.id)
        
        return HttpResponse("Invalid data", status=400)

    return render(request, 'admin_side/variant/add_variant_image.html', {'product_variant': product_variant})


def delete_image(request, image_id):
    try:
        image = Product_variant_images.objects.get(id=image_id)
        image.delete()
        return JsonResponse({'success': True})
    except Product_variant_images.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Image not found'}, status=404)


def variant_detail(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    
    
    variants = Product_Variant.objects.filter(product=product).prefetch_related('product_variant_images_set')
    
    context = {
        'product': product,
        'variants': variants,
    }
    return render(request, 'admin_side/variant/variant_detail.html', context)

@admin_required
def variant_status(request, variant_id):
    variant = get_object_or_404(Product_Variant, id=variant_id)
    variant.variant_status = not variant.variant_status
    variant.save()
    return redirect('product:variant-detail', variant.product.id)



@admin_required
def edit_variant(request, variant_id):
    variant = get_object_or_404(Product_Variant, id=variant_id)
    variant_images = Product_variant_images.objects.filter(product_variant=variant)
    
    if request.method == 'POST':
        variant.size = request.POST.get('variant_size')
        variant.colour_name = request.POST.get('colour_name')
        variant.colour_code = request.POST.get('colour_code')
        variant.variant_stock = request.POST.get('variant_stock')
        variant.variant_status = request.POST.get('variant_status') == 'on'

        if request.FILES.get('images'):
            Product_variant_images.objects.create(
                product_variant=variant,
                images=request.FILES.get('images')
            )
        
        variant.save()
        return redirect('product:variant-detail', variant.product.id)
    
    return render(request, 'admin_side/variant/edit_variant.html', {'variant': variant,'variant_images': variant_images,})


# user side product fuctions

def product_detail_page(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    variants = Product_Variant.objects.filter(product=product).prefetch_related('product_variant_images_set')

    selected_variant = variants.first() 
    variant_images = Product_variant_images.objects.none()
    if selected_variant:
        variant_images = selected_variant.product_variant_images_set.all()

    
    if selected_variant:
        variants = list(variants)
        variants.remove(selected_variant)
        variants.insert(0, selected_variant)

    
    for variant in variants:
        variant.image_urls = ','.join([image.images.url for image in variant.product_variant_images_set.all()])

    
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    user_wishlist = []
    if request.user.is_authenticated:
        user_wishlist = Wishlist.objects.filter(user=request.user).values_list('variant_id', flat=True)

    context = {
        'product': product,
        'variants': variants,
        'selected_variant': selected_variant,
        'variant_images': variant_images,
        'reviews': reviews,
        'average_rating': average_rating,
        'user_wishlist': user_wishlist,
    }

    return render(request, 'user_side/product/product_details2.html', context)


def get_variant_sizes(request):
    variant_id = request.GET.get('variant_id')
    variant = Product_Variant.objects.filter(id=variant_id).first()
    
    if not variant:
        return JsonResponse({'sizes': []}, status=404)  
    
    sizes = []
    size = getattr(variant, 'size', None)
    stock = getattr(variant, 'variant_stock', 0)

    if size:
        sizes.append({'size': size, 'stock': stock})
    
    return JsonResponse({'sizes': sizes})




@login_required(login_url='/login/')
def add_review(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if not rating or not comment:
            return HttpResponse("Rating and comment are required.", status=400)

        Review.objects.create(
            user=request.user,
            product=product,
            rating=rating,
            comment=comment
        )
    return redirect('product:product-detail-page', product_id=product.id)


def shop_page(request):
    brands = Brand.objects.all()
    categories = Category.objects.all()
    

    products = Products.objects.filter(is_active=True)
    search_query = request.GET.get('search_query', '')
    selected_categories = request.GET.getlist('category')
    selected_brands = request.GET.getlist('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if search_query:
        products = products.filter(product_name__icontains=search_query)
    
    
    if selected_categories:
        products = products.filter(product_category__id__in=selected_categories)
    
    if selected_brands:
        products = products.filter(product_brand__id__in=selected_brands)
    
    if min_price:
        products = products.filter(price__gte=min_price)
    
    if max_price:
        products = products.filter(price__lte=max_price)

    sort_by = request.GET.get('sort', 'featured')
    if sort_by == 'price_low_high':
        products = products.order_by('price')
    elif sort_by == 'price_high_low':
        products = products.order_by('-price')
    elif sort_by == 'avg_rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    elif sort_by == 'popularity':
        products = products.annotate(review_count=Count('reviews')).order_by('-review_count')
    elif sort_by == 'new_arrivals':
        products = products.order_by('-created_at')
    elif sort_by == 'name_az':
        products = products.order_by(Lower('product_name'))
    elif sort_by == 'name_za':
        products = products.order_by(Lower('product_name').desc())
    elif sort_by == 'inventory':
        products = products.annotate(
            total_stock=Sum('product_variant__variant_stock')
        ).order_by('-total_stock')

    products = products.prefetch_related(
        Prefetch('product_variant_set', 
                 queryset=Product_Variant.objects.filter(variant_status=True),
                 to_attr='active_variants'),
        'product_variant_set__product_variant_images_set'
    )

    for product in products:
        if product.active_variants:
            variant = product.active_variants[0]
            image = variant.product_variant_images_set.first()
            if image:
                product.image_url = image.images.url
            elif product.thumbnail:
                product.image_url = product.thumbnail.url
            else:
                product.image_url = None 
        elif product.thumbnail:
            product.image_url = product.thumbnail.url
        else:
            product.image_url = None  

    context = {
        'brands': brands,
        'categories': categories,
        'products': products,
        'current_sort': sort_by,
        'selected_categories': selected_categories,
        'selected_brands': selected_brands,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search_query,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        product_html = render_to_string('user_side/product/product_list_partial.html', {'products': products})
        return JsonResponse({'product_html': product_html})
    
    return render(request, 'user_side/product/shop_page.html', context)