from django.urls import path ,include
from . import views

 
app_name = 'brand'

urlpatterns = [

  path('list-brand',views.list_brand,name='list-brand'),
  path('create-brand',views.create_brand,name='create-brand'),
  path('edit-brand/<int:brand_id>/', views.edit_brand, name='edit-brand'),
  path('brand-status/<int:brand_id>/', views.brand_status, name='brand-status'),
]
