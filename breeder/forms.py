from .models import Breeder
from django import forms
from django.utils.translation import gettext_lazy as _


class BreederForm(forms.ModelForm):
    class Meta:
        model = Breeder
        fields = '__all__'
        exclude = ('account',)
        help_texts = {
            'breeding_prefix': _('The name the breeder goes by e.g. Devon Dogs'),
            'contact_name': _('Point of contact for the breeder'),
            'active': _('Is the breeder currently active?'),
        }
        widgets = {
            'breeding_prefix': forms.TextInput(attrs={'required': True, 'class': 'form-control'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number1': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number2': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
        }