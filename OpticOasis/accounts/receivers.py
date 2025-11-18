from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.utils import timezone
from .signals import user_registered

@receiver(user_registered)
def send_welcome_email(sender, user, request, **kwargs):
    otp = get_random_string(length=6, allowed_chars='1234567890')
    otp_generation_time = timezone.now().isoformat()
    request.session['otp'] = otp
    request.session['otp_generation_time'] = otp_generation_time

    text_content = f"Welcome! Your OTP is: {otp}. Valid for 5 minutes."

    html_content = f"""
    <div style="font-family: Arial; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2>Welcome! 🎉</h2>
        <p>Thank you for registering on our platform.</p>
        
        <div style="background: #f0f0f0; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <p style="color: #666; margin: 0;">Your OTP Code</p>
            <div style="background: white; padding: 15px; margin: 15px 0; border-radius: 5px; border: 2px dashed #007bff;">
                <h1 style="font-size: 36px; letter-spacing: 8px; margin: 0; user-select: all; -webkit-user-select: all; -moz-user-select: all;">{otp}</h1>
            </div>
            <p style="color: #666; font-size: 14px; margin: 10px 0;">
         
            </p>
        </div>
        
        <p style="color: #e74c3c; text-align: center;">⏱️ Valid for 2 minutes</p>
        <p style="text-align: center; color: #666; font-size: 14px;">Our Site Team</p>
    </div>
    """
    
    email = EmailMultiAlternatives(
        'Welcome to Our Site - Your OTP Code',
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)