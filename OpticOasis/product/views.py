from django.shortcuts import render,redirect,get_object_or_404
from .models import Products, Category, Brand ,Product_images ,Product_Variant,Product_variant_images 
from utils.decorators import admin_required
from django.http import HttpResponse
from django.utils import timezone
from django.http import JsonResponse
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
        variant_status = request.POST.get('variant_status')
        colour_code = request.POST.get('colour_code')

        variant = Product_Variant.objects.create(
            product=product,
            size=size,
            colour_name=colour_name,
            variant_stock=variant_stock,
            variant_status=variant_status,
            colour_code=colour_code
        )
        

        return redirect('product:add-variant-image', product_variant_id=variant.id)  

    return render(request, 'admin_side/add_variant.html', {'product': product,'variants': variants})


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



def variant_detail(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    
    # Fetch product variants with prefetch related images
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

    selected_variant = variants.first()  # Assuming the first variant is the default one
    variant_images = Product_variant_images.objects.none()
    if selected_variant:
        variant_images = selected_variant.product_variant_images_set.all()

    # Move the selected variant to the beginning of the list
    if selected_variant:
        variants = list(variants)
        variants.remove(selected_variant)
        variants.insert(0, selected_variant)

    # Prepare image URLs for each variant
    for variant in variants:
        variant.image_urls = ','.join([image.images.url for image in variant.product_variant_images_set.all()])

    # Fetch reviews and calculate the average rating
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
        sizes = list(Product_Variant.objects.filter(product=variant.product, colour_code=variant.colour_code).values_list('size', flat=True))
        return JsonResponse({'sizes': sizes})
    else:
        return JsonResponse({'sizes': []}, status=404)


@login_required
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
    return redirect('product_detail', product_id=product.id)