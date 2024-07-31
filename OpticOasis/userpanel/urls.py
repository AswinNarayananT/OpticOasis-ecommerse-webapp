from django.urls import path
from . import views

app_name = 'userpanel'

urlpatterns = [
    path('profile/',views.user_profile,name='user-profile'),
    path('add-address/',views.add_address,name='add-address'),
    path('order-list/',views.user_orders_view,name='order-list'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('order-list/cancel/<int:order_id>/', views.cancel_order, name='cancel-order'),
    path('order-list/return/<int:order_id>/', views.return_order, name='return-order'),
    path('password-change/', views.password_change_view, name='password-change'),
    path('edit-profile/', views.edit_profile, name='edit-profile'),
    path('wallet/', views.wallet_view, name='wallet-view'),
   
]
