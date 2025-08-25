from django import forms
from django.contrib.auth.models import User

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ["username", "email", "password"]

class AddressForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    address_line = forms.CharField(max_length=200)
    city = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=20)
    country = forms.CharField(max_length=2, initial="DE")
