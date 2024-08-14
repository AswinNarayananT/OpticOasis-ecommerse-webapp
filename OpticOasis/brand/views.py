from django.shortcuts import render ,redirect ,get_object_or_404
from .models import Brand
from django.core.files.storage import FileSystemStorage
from utils.decorators import admin_required
from django.contrib import messages

# Create your views here.

@admin_required
def list_brand(request):
    brand = Brand.objects.all().order_by('id')
    return render(request,'admin_side/brand/list_brand.html',{'brand':brand})



@admin_required
def create_brand(request):
    if request.method == 'POST':
        brand_name = request.POST.get('brand_name').strip()
        description = request.POST.get('description', '').strip()
        status = request.POST.get('status') == 'on'
        brand_image = request.FILES.get('brand_image')

        if not brand_name:
            messages.error(request, 'Brand name cannot be empty.')
            return redirect('brand:create-brand')

        if len(brand_name) < 3:
            messages.error(request, 'Brand name must be at least 3 characters long.')
            return redirect('brand:create-brand')

        if Brand.objects.filter(brand_name__iexact=brand_name).exists():
            messages.error(request, 'Brand with this name already exists.')
            return redirect('brand:create-brand')
        
        if brand_image:
            try:
                brand = Brand(
                    brand_name=brand_name,
                    description=description,
                    status=status,
                    brand_image=brand_image
                )
                brand.save()
                messages.success(request, f'Brand "{brand_name}" created successfully.')
            except Exception as e:
                messages.error(request, f'Failed to create brand: {str(e)}')
        else:
            messages.error(request, 'Brand image is required.')

        return redirect('brand:list-brand')
    
    return render(request, 'admin_side/brand/create_brand.html')

@admin_required
def edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    
    if request.method == 'POST':
        brand_name = request.POST.get('brand_name').strip()
        description = request.POST.get('description', '').strip()
        status = request.POST.get('status') == 'on'
        brand_image = request.FILES.get('brand_image')

        if not brand_name:
            messages.error(request, 'Brand name cannot be empty.')
            return redirect('brand:edit-brand', brand_id=brand_id)

        if len(brand_name) < 3:
            messages.error(request, 'Brand name must be at least 3 characters long.')
            return redirect('brand:edit-brand', brand_id=brand_id)

        if Brand.objects.filter(brand_name__iexact=brand_name).exclude(id=brand_id).exists():
            messages.error(request, 'Brand with this name already exists.')
            return redirect('brand:edit-brand', brand_id=brand_id)

        try:
            brand.brand_name = brand_name
            brand.description = description
            brand.status = status
            if brand_image:
                brand.brand_image = brand_image
            brand.save()
            messages.success(request, f'Brand "{brand_name}" updated successfully.')
        except Exception as e:
            messages.error(request, f'Failed to update brand: {str(e)}')

        return redirect('brand:list-brand')

    return render(request, 'admin_side/brand/edit_brand.html', {'brand': brand})
       

@admin_required
def brand_status(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    brand.status = not brand.status
    brand.save()  
    return redirect('brand:list-brand')