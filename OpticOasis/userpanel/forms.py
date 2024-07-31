from django import forms
from django.core.exceptions import ValidationError
from .models import User

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit() or len(phone_number) < 10:
            raise ValidationError("Enter a valid phone number with at least 10 digits.")
        return phone_number
    
    

class OrderActionForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea, required=True, label="Reason for action")
