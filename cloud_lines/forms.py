from .models import Contact
from django.utils.translation import gettext_lazy as _
from django import forms


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = '__all__'
        help_texts = {
            'service': _('If your query is not regarding a service, leave this blank.'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control'}),
        }