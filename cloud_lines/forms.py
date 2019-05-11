from django import forms
from .models import Service


class ContactForm(forms.Form):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True)

    SERVICES = []
    for service in Service.objects.all():
        SERVICES.append((service.service_name, service.service_name))

    service = forms.ChoiceField(choices=SERVICES, required=True)
    subject = forms.CharField(required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)