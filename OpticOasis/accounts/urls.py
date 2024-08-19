from django.urls import path 
from . import views

urlpatterns = [

    path('',views.home_page,name='home_page'),
    path('register/',views.register,name='register'),
    path('verify-otp/',views.verify_otp,name='verify_otp'),
    path('resend-otp/',views.resend_otp,name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('aboutus/', views.about_us, name='about-us'),
    path('contactus/', views.contact_us, name='contact-us'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_request, name='password-reset'),
    path('password-reset-done/', views.password_reset_done, name='password-reset-done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password-reset-confirm'),
    path('reset/done/', views.password_reset_complete, name='password-reset-complete'),
]
