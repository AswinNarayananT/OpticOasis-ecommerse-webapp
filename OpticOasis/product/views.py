from django.shortcuts import render,redirect,get_object_or_404
from .models import Products, Category, Brand ,Product_images ,Product_Variant,Product_variant_images
from utils.decorators import admin_required
from django.http import HttpResponse



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

        product_category = Category.objects.get(id=product_category_id) if product_category_id else None
        product_brand = Brand.objects.get(id=product_brand_id) if product_brand_id else None

        product = Products(
            product_name=product_name,
            product_description=product_description,
            product_category=product_category,
            product_brand=product_brand,
            price=price,
            offer_price=offer_price,
            is_active=is_active
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

        product.save()
        return redirect('product:product-detail',product_id=product_id)

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
            return HttpResponse("Images uploaded successfully")
        
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




