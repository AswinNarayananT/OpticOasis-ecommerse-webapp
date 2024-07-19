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
from django.db.models import Avg




# Create your views here.


@admin_required
def list_product(request):
    products = Products.objects.all().order_by('-created_at') 
    return render(request, 'admin_side/list_product.html', {'products': products})

def product_detail(request, product_id):
    products = get_object_or_404(Products, id=product_id) 
    images = Product_images.objects.filter(product=products)
    return render(request, 'admin_side/product_detail.html', {'products': products, 'images': images})

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
    return render(request, 'admin_side/create_product.html', {'categories': categories, 'brands': brands})

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
    return render(request, 'admin_side/edit_product.html', {'product': product, 'categories': categories, 'brands': brands})


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

    return render(request, 'admin_side/add_images.html', {'product': product})


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

    return render(request, 'admin_side/add_variant.html', {'product': product, 'variants': variants})




def add_variant_image(request, product_variant_id):
    product_variant = get_object_or_404(Product_Variant, id=product_variant_id)
    
    if request.method == 'POST':
        images = request.FILES.getlist('images')
        
        if images:
            for image in images:
                Product_variant_images.objects.create(product_variant=product_variant, images=image)
            return redirect('product:variant-detail', product_id=product_variant.product.id)
        
        return HttpResponse("Invalid data", status=400)

    return render(request, 'admin_side/add_variant_image.html', {'product_variant': product_variant})


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
    return render(request, 'admin_side/variant_detail.html', context)

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
    
    return render(request, 'admin_side/edit_variant.html', {'variant': variant,'variant_images': variant_images,})



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

    context = {
        'product': product,
        'variants': variants,
        'selected_variant': selected_variant,
        'variant_images': variant_images,
        'reviews': reviews,
        'average_rating': average_rating,
    }

    return render(request, 'user_side/product_details2.html', context)


def get_variant_sizes(request):
    variant_id = request.GET.get('variant_id')
    variant = Product_Variant.objects.filter(id=variant_id).first()
    
    if variant:
        variants = Product_Variant.objects.filter(product=variant.product, colour_code=variant.colour_code).values('size', 'variant_stock')
        sizes = [{'size': v['size'], 'stock': v['stock']} for v in variants]
        return JsonResponse({'sizes': sizes})
    else:
        return JsonResponse({'sizes': []}, status=404)


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


# def shop_page(request):
#     brands =Brand.objects.all()
#     categorys=Category.objects.all()
#     products = Products.objects.all()
#     product_variant_images = {}

#     for product in products:
#         variant = Product_Variant.objects.filter(product=product, variant_status=True).first()
#         if variant:
#             image = Product_variant_images.objects.filter(product_variant=variant).first()
#             if image:
#                 product_variant_images[product.id] = image.images.url
                
#                 print(f"Image URL for product {product.id}: {product_variant_images[product.id]}")

#     context = {
#         'brands':brands,
#         'categorys':categorys,
#         'products': products,
#         'product_variant_images': product_variant_images,
#     }
#     return render(request,'user_side/product/shop_page.html',context)


from django.db.models import Avg, Count, Sum, Prefetch
from django.db.models.functions import Lower
from django.http import JsonResponse
from django.template.loader import render_to_string

def shop_page(request):
    brands = Brand.objects.all()
    categories = Category.objects.all()
    
    # Start with all products
    products = Products.objects.filter(is_active=True)
    
    # Filters
    selected_categories = request.GET.getlist('category')
    selected_brands = request.GET.getlist('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if selected_categories:
        products = products.filter(product_category__id__in=selected_categories)
    
    if selected_brands:
        products = products.filter(product_brand__id__in=selected_brands)
    
    if min_price:
        products = products.filter(price__gte=min_price)
    
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
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
    
    # Prefetch related data to optimize queries
    products = products.prefetch_related(
        Prefetch('product_variant_set', 
                 queryset=Product_Variant.objects.filter(variant_status=True),
                 to_attr='active_variants'),
        'product_variant_set__product_variant_images_set'
    )

    # Attach image URLs to products
    for product in products:
        if product.active_variants:
            variant = product.active_variants[0]
            image = variant.product_variant_images_set.first()
            if image:
                product.image_url = image.images.url
            elif product.thumbnail:
                product.image_url = product.thumbnail.url
            else:
                product.image_url = None  # or a default image URL
        elif product.thumbnail:
            product.image_url = product.thumbnail.url
        else:
            product.image_url = None  # or a default image URL

    context = {
        'brands': brands,
        'categories': categories,
        'products': products,
        'current_sort': sort_by,
        'selected_categories': selected_categories,
        'selected_brands': selected_brands,
        'min_price': min_price,
        'max_price': max_price,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        product_html = render_to_string('user_side/product/product_list_partial.html', {'products': products})
        return JsonResponse({'product_html': product_html})
    
    return render(request, 'user_side/product/shop_page.html', context)


# from django.shortcuts import render
# from .models import Products, Product_Variant, Product_variant_images

# def shop_page(request):
#     brands = Brand.objects.all()
#     categorys = Category.objects.all()
#     products = Products.objects.all()

#     # Create a dictionary to store product variant images
#     product_variant_images = {}

#     # Function to get product variant image URL
#     def get_product_variant_image(product):
#         variant = Product_Variant.objects.filter(product=product, variant_status=True).first()
#         if variant:
#             image = Product_variant_images.objects.filter(product_variant=variant).first()
#             if image:
#                 return image.images.url  # Return the image URL
#         return None  # Return None if no image found

#     # Populate product variant images dictionary
#     for product in products:
#         product_variant_images[product.id] = get_product_variant_image(product)

#     context = {
#         'brands': brands,
#         'categorys': categorys,
#         'products': products,
#         'product_variant_images': product_variant_images,
#     }
#     return render(request, 'user_side/product/shop_page.html', context)


# def filter_products(request):
#     category_ids = request.GET.getlist('category_ids[]', [])
#     brand_ids = request.GET.getlist('brand_ids[]', [])
#     sort_by = request.GET.get('sort_by', None)
#     price_range = request.GET.get('price_range', None)

#     products = Products.objects.all()

#     if category_ids:
#         products = products.filter(category__id__in=category_ids)

#     if brand_ids:
#         products = products.filter(brand__id__in=brand_ids)

#     if sort_by == 'popularity':
#         # Implement your popularity sorting logic here
#         products = products.order_by('-popularity')

#     elif sort_by == 'average_rating':
#         # Implement your average rating sorting logic here
#         products = products.order_by('-average_rating')

#     elif sort_by == 'price_low_high':
#         # Implement your price low to high sorting logic here
#         products = products.order_by('price')

#     elif sort_by == 'price_high_low':
#         # Implement your price high to low sorting logic here
#         products = products.order_by('-price')

#     # Implement price range filtering logic if applicable
#     if price_range == '0-200':
#         products = products.filter(price__range=(0, 200))

#     elif price_range == '200-400':
#         products = products.filter(price__range=(200, 400))

#     elif price_range == '400-600':
#         products = products.filter(price__range=(400, 600))

#     elif price_range == '600-800':
#         products = products.filter(price__range=(600, 800))

#     elif price_range == '800+':
#         products = products.filter(price__gte=800)

#     context = {
#         'products': products,
#         'product_variant_images': get_product_variant_images(products),
#     }

#     # Render products HTML snippet and return as JSON response
#     html_products = render_to_string('user_side/product/product_grid.html', context, request=request)
#     return JsonResponse({'html_products': html_products})

# def get_product_variant_images(products):
#     product_variant_images = {}
#     for product in products:
#         variant = Product_Variant.objects.filter(product=product, variant_status=True).first()
#         if variant:
#             image = Product_variant_images.objects.filter(product_variant=variant).first()
#             if image:
#                 product_variant_images[product.id] = image.images.url
#     return product_variant_images

