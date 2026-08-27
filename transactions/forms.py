from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    accept_terms = forms.BooleanField(
        required=True,
        label='I have read and accept the thrift shop terms and conditions.',
    )

    class Meta:
        model = Customer
        fields = ['name', 'email', 'cpf']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email address'}),
            'cpf': forms.TextInput(attrs={'placeholder': 'CPF', 'inputmode': 'numeric'}),
        }
