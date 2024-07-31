from django.urls import path 
from . import views

urlpatterns = [

    path('',views.home_page,name='home_page'),
    path('register/',views.register,name='register'),
    path('verify-otp/',views.verify_otp,name='verify_otp'),
    path('resend-otp/',views.resend_otp,name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
