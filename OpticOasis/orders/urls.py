from django.urls import path ,include
from . import views

 
app_name = 'orders'

urlpatterns = [

  path('order-placed/', views.order_placed, name='order-placed'),
  path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order-confirmation'),
  path('add-address/', views.add_address, name='add-address'),

]
