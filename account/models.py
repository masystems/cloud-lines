from django.db import models
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SiteDetail(models.Model):

    animal_type = models.CharField(max_length=250)

    SITE_MODES = (
        ('mammal', 'Mammal'),
        ('poultry', 'Poultry'),
    )
    site_mode = models.CharField(max_length=13, choices=SITE_MODES, default=None)

    install_available = models.BooleanField(default=True)

    def __str__(self):
        return self.site_mode


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )


class UserDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owner')
    phone = models.TextField(max_length=15, blank=False)

