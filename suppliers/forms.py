import re

from django import forms

from .models import Supplier


class SupplierRegistrationForm(forms.ModelForm):
    accept_terms = forms.BooleanField(required=True, label='I have read and accept the consignment terms.')

    class Meta:
        model = Supplier
        fields = ('name', 'email', 'cpf', 'pix_key')
        labels = {'name': 'Full name', 'email': 'Email address', 'cpf': 'CPF', 'pix_key': 'PIX key'}
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your full name', 'autocomplete': 'name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@example.com', 'autocomplete': 'email'}),
            'cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00', 'inputmode': 'numeric'}),
            'pix_key': forms.TextInput(attrs={'placeholder': 'CPF, email, phone or random key'}),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf'].strip()
        digits = re.sub(r'\D', '', cpf)
        if len(digits) != 11:
            raise forms.ValidationError('Enter a CPF with 11 digits.')
        return f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}'
