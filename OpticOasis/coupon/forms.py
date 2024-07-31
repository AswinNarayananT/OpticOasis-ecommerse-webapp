from django import forms
from django.utils import timezone
from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['coupon_name', 'coupon_code', 'minimum_amount', 'discount', 'maximum_amount', 'expiry_date', 'status']
        widgets = {
            'coupon_name': forms.TextInput(attrs={'class': 'form-control'}),
            'coupon_code': forms.TextInput(attrs={'class': 'form-control'}),
            'minimum_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control'}),
            'maximum_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


    def clean_coupon_name(self):
        name = self.cleaned_data.get('coupon_name')
        if len(name) < 3:
            raise forms.ValidationError("Coupon name must be at least 3 characters long.")
        return name

    def clean_minimum_amount(self):
        min_amount = self.cleaned_data.get('minimum_amount')
        if min_amount < 0:
            raise forms.ValidationError("Minimum amount cannot be negative.")
        return min_amount

    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount <= 0:
            raise forms.ValidationError("Discount must be greater than zero.")
        return discount

    def clean_maximum_amount(self):
        max_amount = self.cleaned_data.get('maximum_amount')
        if max_amount < 0:
            raise forms.ValidationError("Maximum amount cannot be negative.")
        return max_amount

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date')
        if expiry_date and expiry_date < timezone.now().date():
            raise forms.ValidationError("Expiry date cannot be in the past.")
        return expiry_date

    def clean_coupon_code(self):
        code = self.cleaned_data.get('coupon_code')
        if not code.isalnum():
            raise forms.ValidationError("Coupon code must contain only letters and numbers.")
        return code.upper() 

    def clean(self):
        cleaned_data = super().clean()
        minimum_amount = cleaned_data.get('minimum_amount')
        maximum_amount = cleaned_data.get('maximum_amount')
        discount = cleaned_data.get('discount')

        if maximum_amount and minimum_amount and maximum_amount < minimum_amount:
            raise forms.ValidationError("Maximum amount cannot be less than minimum amount.")

        if discount and minimum_amount and discount > minimum_amount:
            raise forms.ValidationError("Discount cannot be greater than minimum amount.")

        if maximum_amount and discount and discount > maximum_amount:
            raise forms.ValidationError("Discount cannot be greater than maximum amount.")

        return cleaned_data