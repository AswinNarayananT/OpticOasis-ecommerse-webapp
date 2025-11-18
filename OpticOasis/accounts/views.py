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
from .forms import EmailAuthenticationForm
from brand.models import Brand
from category.models import Category
from product.models import Products
from .signals import user_registered
from django.core.mail import send_mail
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import SetPasswordForm
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site




# Create your views here.

User = get_user_model()

def home_page(request):
    brands =Brand.objects.all()
    categories=Category.objects.all()
    products =Products.objects.filter(is_active=True)
    return render(request,'user_side/account/index-3.html',{'brands':brands,'categories':categories,'products':products})

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

        # HTML email content
        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color:#333;">Your New OTP Code</h2>
            <p>We received a request to resend your One-Time Password (OTP).</p>

            <div style="font-size: 24px; font-weight: bold; 
                        background:#f3f3f3; padding: 12px 18px; 
                        border-radius: 6px; width: fit-content;
                        letter-spacing: 3px; margin: 10px 0;">
                {otp}
            </div>

            <!-- Copy Button -->
            <a href="#" 
               onclick="navigator.clipboard.writeText('{otp}'); alert('OTP copied to clipboard!'); return false;"
               style="
                    display:inline-block;
                    padding:10px 18px;
                    background:#007bff;
                    color:white; 
                    text-decoration:none; 
                    border-radius:5px;
                    font-size:14px;">
                Copy OTP
            </a>

            <p style="margin-top:20px;">This OTP is valid for <strong>5 minutes</strong>.</p>

            <p style="color:red; font-size:13px;">
                ⚠️ For your security, please do not share this OTP with anyone.
            </p>

            <p>If you didn’t request this, you can safely ignore this message.</p>

            <p>Thank you,<br>The Support Team</p>
        </div>
        """

        # fallback plain text
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject="Your New OTP Code",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_data['email']],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

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


def about_us(request):
   return render(request,'user_side/account/aboutus.html') 

def contact_us(request):
    return render(request,'user_side/account/contact.html') 

def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        current_site = get_current_site(request)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "user_side/account/password_reset_email.txt"
                    c = {
                        "email": user.email,
                        'domain': current_site.domain,
                        'site_name': 'Optic Oasis',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email_content = render_to_string(email_template_name, c)
                    try:
                        send_mail(
                            subject,
                            email_content,
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            fail_silently=False,
                        )
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    return redirect("password-reset-done")
    
    password_reset_form = PasswordResetForm()
    return render(request, "user_side/account/password_reset.html", {"password_reset_form": password_reset_form})


def password_reset_done(request):
    return render(request, 'user_side/account/password_reset_done.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been set. You may go ahead and log in now.')
                return redirect('password-reset-complete')
        else:
            form = SetPasswordForm(user)
        return render(request, 'user_side/account/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'The password reset link was invalid, possibly because it has already been used. Please request a new password reset.')
        return redirect('password-reset')

def password_reset_complete(request):
    return render(request, 'user_side/account/password_reset_complete.html')


