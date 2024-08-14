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
    path('edit-variant/<int:variant_id>/',views.edit_variant, name='edit-variant'),
     path('delete-image/<int:image_id>/',views.delete_image, name='delete-image'),
    path('variant-status/<int:variant_id>/',views.variant_status, name='variant-status'),
    path('product/<int:product_id>/', views.product_detail_page, name='product-detail-page'),
    path('get-variant-sizes/', views.get_variant_sizes, name='get-variant-sizes'),
    path('add-review/<int:product_id>/',views.add_review, name='add-review'),
    path('shop-page',views.shop_page, name='shop-page'),
  
]
