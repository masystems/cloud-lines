from .models import Breeder
from django import forms
from django.utils.translation import gettext_lazy as _


class BreederForm(forms.ModelForm):
    class Meta:
        model = Breeder
        fields = '__all__'
        exclude = ('account', 'user')
        help_texts = {
            'breeding_prefix': _('The name the breeder goes by e.g. Devon Dogs'),
            'contact_name': _('Point of contact for the breeder'),
            'active': _('Is the breeder currently active?'),
        }
        widgets = {
            'breeding_prefix': forms.TextInput(attrs={'required': True, 'class': 'form-control', 'id': 'id_breeding_prefix'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_contact_name'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_address_line_1'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_address_line_2'}),
            'town': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_town'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_country'}),
            'postcode': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_postcode'}),
            'phone_number1': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_phone_number1'}),
            'phone_number2': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_phone_number2'}),
            'email': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_email'}),
            'data_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }