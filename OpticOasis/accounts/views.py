import random
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .forms import UserRegistrationForm
from django.contrib import messages
from django.utils.crypto import get_random_string
from .models import User
from datetime import timedelta
from django.views.decorators.csrf import csrf_protect
from dateutil.parser import parse
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import EmailAuthenticationForm
from brand.models import Brand
from category.models import Category
from product.models import Products,Product_images,Product_Variant
from .signals import user_registered
from django.core.exceptions import ValidationError


# Create your views here.

User = get_user_model()

def home_page(request):
    brands =Brand.objects.all()
    categorys=Category.objects.all()
    products =Products.objects.filter(is_active=True)
    return render(request,'user_side/account/index-3.html',{'brands':brands,'categorys':categorys,'products':products})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user_data = form.save(commit=False)      
            user_data.is_active = False

            request.session['user_data'] = {
                'first_name': user_data.first_name,
                'last_name': user_data.last_name,
                'email': user_data.email,
                'phone_number': user_data.phone_number,
                'password': form.cleaned_data.get('password')  
            }
            
            user_registered.send(sender=register, user=user_data, request=request)

            messages.success(request, 'OTP has been sent to your email. Please verify to complete registration.')
            return redirect('verify_otp')
    else:
        form = UserRegistrationForm()
    return render(request, 'user_side/account/user_register.html', {'form': form})

@csrf_protect
def verify_otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        otp_generation_time_str = request.session.get('otp_generation_time')

        if otp_generation_time_str:
            try:
                otp_generation_time = parse(otp_generation_time_str)
                current_time = timezone.now()
                otp_valid_duration = timedelta(minutes=2)

                if current_time - otp_generation_time <= otp_valid_duration:
                    if otp == request.session.get('otp'):
                        user_data = request.session.get('user_data')
                        if user_data:
                            user = User.objects.create(
                                first_name=user_data.get('first_name'),
                                last_name=user_data.get('last_name'),
                                email=user_data.get('email'),
                                phone_number=user_data.get('phone_number')
                            )
                            user.set_password(user_data.get('password'))  
                            user.is_active = True
                            user.save()

                            
                            request.session.flush()

                            messages.success(request, 'Your account has been activated successfully.')
                            return redirect('login') 
                        else:
                            messages.error(request, 'User data not found. Please register again.')
                    else:
                        messages.error(request, 'Invalid OTP. Please try again.')
                else:
                    messages.error(request, 'OTP has expired. Please resent OTP.')
            except ValueError:
                messages.error(request, 'Invalid OTP generation time format.')
        else:
            messages.error(request, 'OTP generation time not found. Please register again.')

    return render(request, 'user_side/account/verify_otp.html')

def resend_otp(request):
    user_data = request.session.get('user_data')
    if user_data:
        otp = get_random_string(length=6, allowed_chars='1234567890')
        print(otp)
        otp_generation_time = timezone.now().isoformat()
        
        request.session['otp'] = otp
        request.session['otp_generation_time'] = otp_generation_time

        send_mail(
            'Your OTP Code',
            f'Your OTP code is {otp}',
            settings.DEFAULT_FROM_EMAIL,
            [user_data['email']],
            fail_silently=False,
        )
        messages.success(request, 'A new OTP has been sent to your email.')
    else:
        messages.error(request, 'User data not found. Please register again.')
    return redirect('verify_otp')


def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_active and not user.is_blocked:  
                login(request, user)
                messages.success(request, f"Welcome, {user.email}! You have successfully logged in.")
                return redirect('home_page')
            else:
                messages.error(request, "This account is inactive. Please contact support.")
        else:
            messages.error(request, "Invalid email or password. Please try again.")
    else:
        form = EmailAuthenticationForm()
    return render(request, 'user_side/account/user_login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('home_page')

        