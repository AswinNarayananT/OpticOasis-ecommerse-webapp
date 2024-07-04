from django.shortcuts import render ,redirect ,get_object_or_404
from .models import Brand
from django.core.files.storage import FileSystemStorage
from utils.decorators import admin_required
from django.contrib import messages

# Create your views here.

@admin_required
def list_brand(request):
    brand = Brand.objects.all().order_by('id')
    return render(request,'admin_side/list_brand.html',{'brand':brand})



@admin_required
def create_brand(request):
    if request.method == 'POST':
        brand_name = request.POST.get('brand_name')
        description = request.POST.get('description', '')
        status = request.POST.get('status') == 'on'
        brand_image = request.FILES.get('brand_image')

        if brand_name and brand_image:
            if Brand.objects.filter(brand_name=brand_name).exists():
                messages.error(request, 'Brand with this name already exists.')
            else:
                brand = Brand(
                    brand_name=brand_name,
                    description=description,
                    status=status,
                    brand_image=brand_image
                )
                brand.save()
            return redirect('brand:list-brand')

    return render(request, 'admin_side/create_brand.html')

@admin_required
def edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    if request.method == 'POST':
        brand_name = request.POST.get('brand_name')
        description = request.POST.get('description')
        status = request.POST.get('status')
        brand_image = request.FILES.get('brand_image')

        if Brand.objects.filter(brand_name=brand_name).exclude(id=brand_id).exists():
                messages.error(request, 'Brand with this name already exists.')
        else:        
            brand.brand_name = brand_name
            brand.description = description
            brand.status = status
            if brand_image:
                brand.brand_image = brand_image

            brand.save()
        return redirect('brand:list-brand')

    return render(request, 'admin_side/edit_brand.html', {'brand': brand})
       

@admin_required
def brand_status(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    brand.status = not brand.status
    brand.save()  
    return redirect('brand:list-brand')