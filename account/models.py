from django.db import models
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from cloud_lines.models import Service


class SiteDetail(models.Model):

    admin_users = models.ManyToManyField(User, related_name='admin_users')
    read_only_users = models.ManyToManyField(User, related_name='read_only_users')
    animal_type = models.CharField(max_length=250)

    SITE_MODES = (
        ('mammal', 'Mammal'),
        ('poultry', 'Poultry'),
    )
    site_mode = models.CharField(max_length=13, choices=SITE_MODES, default=None)

    install_available = models.BooleanField(default=True)

    def __str__(self):
        return self.animal_type


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )


class UserDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user')
    phone = models.CharField(max_length=15, blank=False)
    stripe_id = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return str(self.user)


class AttachedService(models.Model):
    user = models.ForeignKey(UserDetail, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    site_detail = models.ForeignKey(SiteDetail, on_delete=models.SET_NULL, null=True, blank=True)
    INCREMENTS = (
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )
    increment = models.CharField(max_length=10, choices=INCREMENTS, default=None, null=True, blank=True)
    active = models.BooleanField(default=False)
