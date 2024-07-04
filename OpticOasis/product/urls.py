from django.urls import path 
from . import views

app_name = 'product'

urlpatterns = [

    path('products/',views.list_product,name='list-product'),
    path('create/',views.create_product,name='create-product'),
    path('edit/<int:product_id>',views.edit_product,name='edit-product'),
    path('status/<int:product_id>',views.product_status,name='product-status'),
    path('add-images/<int:product_id>',views.add_images,name='add-images'),
    path('add-variant/<int:product_id>',views.add_variant,name='add-variant'),
    path('product_detail/<int:product_id>',views.product_detail,name='product-detail'),
    path('variant/<int:product_id>/', views.variant_detail, name='variant-detail'),
    path('add-variant-image/<int:product_variant_id>/',views.add_variant_image, name='add-variant-image'),
    

]
