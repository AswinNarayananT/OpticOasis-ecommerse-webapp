from django.urls import path ,include
from . import views

 
app_name = 'orders'

urlpatterns = [

  path('order-placed/', views.order_placed, name='order-placed'),
  path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order-confirmation'),
  path('add-address/', views.add_address, name='add-address'),
  path('order-list/', views.admin_order_list, name='list-order'),
  path('admin-orders-details/<int:oid>', views.admin_orders_details, name='admin-orders-details'),
  path('razorpay/callback/', views.razorpay_callback, name='razorpay-callback'),
  path('failure/<int:order_id>/', views.order_failure, name='order-failure'),
  path('change-order-status/<int:order_id>/', views.change_order_status, name='change_order_status'),
  
]
