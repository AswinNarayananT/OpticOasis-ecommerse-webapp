from django import forms
from django.core.exceptions import ValidationError
from .models import User ,UserAddress


class UserAddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = [
            'name', 'house_name', 'street_name', 'pin_number', 
            'district', 'state', 'country', 'phone_number', 'status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'house_name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'street_name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'pin_number': forms.NumberInput(attrs={'class': 'form-control', 'required': 'required'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_pin_number(self):
        pin_number = self.cleaned_data.get('pin_number')
        if len(str(pin_number)) != 6:
            raise ValidationError("Pin number must be 6 digits long.")
        return pin_number

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if len(phone_number) < 10 or len(phone_number) > 15:
            raise ValidationError("Phone number must be between 10 to 15 digits.")
        if not phone_number.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        return phone_number

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name.isalpha():
            raise ValidationError("Name should only contain letters.")
        return name

    def clean_district(self):
        district = self.cleaned_data.get('district')
        if not district.isalpha():
            raise ValidationError("District should only contain letters.")
        return district

    def clean_state(self):
        state = self.cleaned_data.get('state')
        if not state.isalpha():
            raise ValidationError("State should only contain letters.")
        return state

    def save(self, commit=True):
        if self.cleaned_data.get('status'):
            UserAddress.objects.filter(user=self.instance.user, status=True).update(status=False)

        return super().save(commit=commit)

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
