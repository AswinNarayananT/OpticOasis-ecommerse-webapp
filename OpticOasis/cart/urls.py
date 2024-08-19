from django.urls import path ,include
from . import views

app_name = 'cart'

urlpatterns = [
    
    path('cart/',views.cart_view,name='cart-view'),
    path('add-to-cart/',views.add_to_cart,name='add-to-cart'),
    path('remove-item/<int:item_id>/',views.remove_item, name='remove-item'),
    path('update-cart-quantity/',views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('button/',views.check_cart_status, name='button'),
    path('add-address/',views.add_address, name='add-address'),
    path('update-counts/',views.update_counts, name='update-counts'),
    
]

