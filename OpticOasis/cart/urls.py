from django.urls import path ,include
from . import views

app_name = 'cart'

urlpatterns = [
    
    path('cart/',views.cart_view,name='cart-view'),
    path('add-to-cart/',views.add_to_cart,name='add-to-cart'),
    path('remove-item/<int:item_id>/', views.remove_item, name='remove-item'),
]

