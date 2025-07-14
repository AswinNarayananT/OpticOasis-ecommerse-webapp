from .models import Products, Category, Brand ,Product_images ,Product_Variant,Product_variant_images ,Review
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Avg, Count, Sum
from django.template.loader import render_to_string
from django.http import JsonResponse ,HttpResponse
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower
from utils.decorators import admin_required
from cart.models import Cart, CartItem
from userpanel.models import Wishlist
from django.contrib import messages
from django.utils import timezone
from django.db import DataError
import json
import re


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

        stripped_product_name = product_name.strip()
        stripped_product_description = product_description.strip()
        stripped_price = price.strip() if price else '0'
        stripped_offer_price = offer_price.strip() if offer_price else '0'

        if not re.match("^[A-Za-z ]+$", stripped_product_name):
            messages.error(request, 'Product name must contain only letters and spaces.')
            return redirect('product:create-product')
        
        if len(stripped_product_name) < 3:
            messages.error(request, 'Product name must be at least 3 characters long.')
            return redirect('product:create-product')

        try:
            price = float(stripped_price)
            offer_price = float(stripped_offer_price)
            if price < 0 or offer_price < 0:
                raise ValidationError('Price and Offer Price cannot be negative.')
            if offer_price > price:
                raise ValidationError('Offer price cannot be greater than the regular price.')
        except ValueError:
            messages.error(request, 'Price and Offer Price must be valid numbers.')
            return redirect('product:create-product')
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('product:create-product')

        if Products.objects.filter(product_name__iexact=stripped_product_name).exists():
            messages.error(request, f'Product with the name "{stripped_product_name}" already exists.')
            return redirect('product:create-product')

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

        messages.success(request, f'Product "{product_name}" created successfully.')
        return redirect('product:list-product')

    categories = Category.objects.all()
    brands = Brand.objects.all()
    return render(request, 'admin_side/product/create_product.html', {'categories': categories, 'brands': brands})



@admin_required
def edit_product(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        product_description = request.POST.get('product_description')
        product_category_id = request.POST.get('product_category')
        product_brand_id = request.POST.get('product_brand')
        price = request.POST.get('price').strip()
        offer_price = request.POST.get('offer_price').strip()
        is_active = request.POST.get('is_active') == 'on'
        thumbnail = request.FILES.get('thumbnail')

        stripped_product_name = product_name.strip()
        stripped_product_description = product_description.strip()

        if not re.match("^[A-Za-z ]+$", stripped_product_name):
            messages.error(request, 'Product name must contain only letters and spaces.')
            return redirect('product:edit-product', product_id=product_id)

        if len(stripped_product_name) < 3:
            messages.error(request, 'Product name must be at least 3 characters long.')
            return redirect('product:edit-product', product_id=product_id)

        try:
            price = float(price)
            offer_price = float(offer_price)
            if price < 0 or offer_price < 0:
                raise ValidationError('Price and Offer Price cannot be negative.')
            if offer_price > price:
                raise ValidationError('Offer price cannot be greater than the regular price.')
        except ValueError:
            messages.error(request, 'Price and Offer Price must be valid numbers.')
            return redirect('product:edit-product', product_id=product_id)
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('product:edit-product', product_id=product_id)

        if Products.objects.filter(product_name__iexact=product_name).exclude(id=product_id).exists():
            messages.error(request, f'Product with the name "{stripped_product_name}" already exists.')
            return redirect('product:edit-product', product_id=product_id)

        product.product_name = product_name
        product.product_description = product_description
        product.price = price
        product.offer_price = offer_price
        product.is_active = is_active

        if thumbnail:
            product.thumbnail = thumbnail

        product.product_category = Category.objects.get(id=product_category_id) if product_category_id else None
        product.product_brand = Brand.objects.get(id=product_brand_id) if product_brand_id else None

        product.updated_at = timezone.now() 
        product.save()

        messages.success(request, f'Product "{product_name}" updated successfully.')
        return redirect('product:product-detail', product_id=product_id)

    categories = Category.objects.all()
    brands = Brand.objects.all()
    return render(request, 'admin_side/product/edit_product.html', {
        'product': product, 
        'categories': categories, 
        'brands': brands,
    })


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
        variant_status = request.POST.get('variant_status')
        colour_code = request.POST.get('colour_code')

        if not size:
            messages.error(request, 'Size is required.')
            return redirect('product:add-variant', product_id=product_id)

        stripped_colour_name = colour_name.strip()
        if not re.match("^[A-Za-z ]+$", stripped_colour_name):
            messages.error(request, 'Color name must contain only letters and spaces.')
            return redirect('product:add-variant', product_id=product_id)

        try:
            variant_stock = int(variant_stock)
            if variant_stock < 0:
                raise ValidationError('Variant stock cannot be negative.')
        except ValueError:
            messages.error(request, 'Variant stock must be a valid number.')
            return redirect('product:add-variant', product_id=product_id)
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('product:add-variant', product_id=product_id)

        if variant_status not in ['0', '1']:
            messages.error(request, 'Invalid variant status.')
            return redirect('product:add-variant', product_id=product_id)
        variant_status = bool(int(variant_status))

        name_exists = Product_Variant.objects.filter(
            product=product,
            colour_name=stripped_colour_name
        ).exists()

        if name_exists:
            messages.error(request, 'A variant with this color name already exists.')
            return redirect('product:add-variant', product_id=product_id)

        code_exists = Product_Variant.objects.filter(
            product=product,
            colour_code=colour_code
        ).exists()

        if code_exists:
            messages.error(request, 'A variant with this color code already exists.')
            return redirect('product:add-variant', product_id=product_id)

        variant = Product_Variant.objects.create(
            product=product,
            size=size,
            colour_name=colour_name,
            variant_stock=variant_stock,
            variant_status=variant_status,
            colour_code=colour_code
        )

        messages.success(request, 'Variant added successfully.')
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
        size = request.POST.get('variant_size')
        colour_name = request.POST.get('colour_name')
        colour_code = request.POST.get('colour_code')
        variant_stock = request.POST.get('variant_stock')
        variant_status = request.POST.get('variant_status') == 'on'

        stripped_colour_name = colour_name.strip() if colour_name else ''
        stripped_colour_code = colour_code.strip() if colour_code else ''

        if not re.match("^[A-Za-z ]+$", stripped_colour_name):
            messages.error(request, 'Color name must contain only letters and spaces.')
            return redirect('product:edit-variant', variant_id=variant_id)


        if not stripped_colour_code:
            messages.error(request, 'Color code is required.')
            return redirect('product:edit-variant', variant_id=variant_id)

        if Product_Variant.objects.filter(product=variant.product, colour_name=stripped_colour_name).exclude(id=variant_id).exists():
            messages.error(request, 'A variant with this color name already exists.')
            return redirect('product:edit-variant', variant_id=variant_id)

        if Product_Variant.objects.filter(product=variant.product, colour_code=stripped_colour_code).exclude(id=variant_id).exists():
            messages.error(request, 'A variant with this color code already exists.')
            return redirect('product:edit-variant', variant_id=variant_id)

        try:
            variant_stock = int(variant_stock)
            if variant_stock < 0:
                raise ValidationError('Stock cannot be negative.')
        except ValueError:
            messages.error(request, 'Stock must be a valid integer.')
            return redirect('product:edit-variant', variant_id=variant_id)
        except ValidationError as e:
            messages.error(request, str(e))

        if not stripped_colour_name:
            messages.error(request, 'Color name is required.')
            return redirect('product:edit-variant', variant_id=variant_id)

        if not stripped_colour_code:
            messages.error(request, 'Color code is required.')
            return redirect('product:edit-variant', variant_id=variant_id)

        variant.size = size
        variant.colour_name = stripped_colour_name
        variant.colour_code = stripped_colour_code
        variant.variant_stock = variant_stock
        variant.variant_status = variant_status

        if request.FILES.get('images'):
            Product_variant_images.objects.create(
                product_variant=variant,
                images=request.FILES.get('images')
            )
        
        try:
            variant.save()
            messages.success(request, 'Variant updated successfully.')
        except DataError:
            messages.error(request, 'The value for one or more fields is out of range.')
            return redirect('product:edit-variant', variant_id=variant_id)

        return redirect('product:variant-detail', variant.product.id)

    return render(request, 'admin_side/variant/edit_variant.html', {'variant': variant, 'variant_images': variant_images})





# user side product fuctions

def product_detail_page(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    star_ratings = product.get_star_rating_distribution()
    variants = Product_Variant.objects.filter(product=product).prefetch_related('product_variant_images_set')
    related_products = Products.objects.filter(product_brand=product.product_brand).exclude(id=product_id)[:4]

    has_purchased = False 
    if request.user.is_authenticated:
        has_purchased = product.user_has_purchased(request.user) 

    selected_variant = variants.first() 
    variant_images = Product_variant_images.objects.none()
    if selected_variant:
        variant_images = selected_variant.product_variant_images_set.all()

    
    if selected_variant:
        variants = list(variants)
        variants.remove(selected_variant)
        variants.insert(0, selected_variant)

    
    for variant in variants:
        variant.image_urls = [image.images.url for image in variant.product_variant_images_set.all()[:5]]

    
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
        'star_ratings': star_ratings,
        'has_purchased': has_purchased,
        'related_products': related_products,
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


def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    if review.user == request.user:
        review.delete()
        messages.success(request, 'Your review has been deleted.')
    else:
        messages.error(request, 'You are not authorized to delete this review.')

    return redirect('product:product-detail-page', product_id=review.product.id)



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
    sort_options = {
        'price_low_high': 'price',
        'price_high_low': '-price',
        'avg_rating': '-avg_rating',
        'popularity': '-review_count',
        'new_arrivals': '-created_at',
        'name_az': Lower('product_name'),
        'name_za': Lower('product_name').desc(),
        'inventory': '-total_stock'
    }

    if sort_by in sort_options:
        if sort_by == 'avg_rating':
            products = products.annotate(avg_rating=Avg('-reviews__rating')).order_by(sort_options[sort_by])
        elif sort_by == 'popularity':
            products = products.annotate(review_count=Count('reviews')).order_by(sort_options[sort_by])
        elif sort_by == 'inventory':
            products = products.annotate(total_stock=Sum('product_variant__variant_stock')).order_by(sort_options[sort_by])
        else:
            products = products.order_by(sort_options[sort_by])

    products = products.prefetch_related(
        Prefetch('product_variant_set',
                 queryset=Product_Variant.objects.filter(variant_status=True),
                 to_attr='active_variants'),
        'product_variant_set__product_variant_images_set'
    )

    paginator = Paginator(products, 6)
    page = request.GET.get('page')

    try:
        products_paginated = paginator.page(page)
    except PageNotAnInteger:
        products_paginated = paginator.page(1)
    except EmptyPage:
        products_paginated = paginator.page(paginator.num_pages)

    for product in products_paginated:
        if product.active_variants:
            variant = product.active_variants[0]
            image = variant.product_variant_images_set.first()
            product.image_url = image.images.url if image else product.thumbnail.url if product.thumbnail else None
        else:
            product.image_url = product.thumbnail.url if product.thumbnail else None

    context = {
        'brands': brands,
        'categories': categories,
        'products': products_paginated,
        'current_sort': sort_by,
        'selected_categories': selected_categories,
        'selected_brands': selected_brands,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search_query,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('user_side/product/product_list_partial.html', {'products': products_paginated})
        return JsonResponse({'html': html})
    
    return render(request, 'user_side/product/shop_page.html', context)

def parse_request_body(request):
    body_unicode = request.body.decode('utf-8')
    return json.loads(body_unicode)

@login_required(login_url='/login/')
def check_status(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    variant = Product_Variant.objects.filter(product=product).first()

    cart = Cart.objects.filter(user=request.user).first()
    in_cart = False
    if cart:
        in_cart = CartItem.objects.filter(cart=cart, variant=variant, is_active=True).exists()

    in_wishlist = Wishlist.objects.filter(user=request.user, variant=variant).exists()

    return JsonResponse({"in_cart": in_cart, "in_wishlist": in_wishlist})

@login_required(login_url='/login/')
def toggle_cart(request):
    if request.method == "POST":
        data = parse_request_body(request)
        product_id = data.get("product_id")
        product = get_object_or_404(Products, id=product_id)
        variant = Product_Variant.objects.filter(product=product).first()

        cart, _ = Cart.objects.get_or_create(user=request.user)

        existing_item = CartItem.objects.filter(cart=cart, variant=variant, is_active=True).first()

        if existing_item:
            existing_item.is_active = False
            existing_item.save()
            return JsonResponse({"status": "removed"})
        else:
            CartItem.objects.filter(cart=cart, variant=variant).update(is_active=False)

            CartItem.objects.create(cart=cart, product=product, variant=variant, quantity=1, is_active=True)
            return JsonResponse({"status": "added"})

    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required(login_url='/login/')
def toggle_wishlist(request):
    if request.method == "POST":
        data = parse_request_body(request)
        product_id = data.get("product_id")
        product = get_object_or_404(Products, id=product_id)
        variant = Product_Variant.objects.filter(product=product).first()

        existing = Wishlist.objects.filter(user=request.user, variant=variant).first()

        if existing:
            existing.delete()
            return JsonResponse({"status": "removed"})
        else:
            Wishlist.objects.create(user=request.user, variant=variant)
            return JsonResponse({"status": "added"})

    return JsonResponse({"error": "Invalid request"}, status=400)