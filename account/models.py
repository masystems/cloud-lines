from django.db import models
from django.contrib.auth.models import User
from cloud_lines.models import Service


class UserDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user')
    phone = models.CharField(max_length=15, blank=False)
    stripe_id = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return str(self.user)


class AttachedService(models.Model):
    user = models.OneToOneField(UserDetail, on_delete=models.CASCADE, related_name='attached_service', null=True, blank=True)
    admin_users = models.ManyToManyField(User, related_name='admin_users', blank=True)
    read_only_users = models.ManyToManyField(User, related_name='read_only_users', blank=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    animal_type = models.CharField(max_length=250)

    SITE_MODES = (
        ('mammal', 'Mammal'),
        ('poultry', 'Poultry'),
    )
    site_mode = models.CharField(max_length=13, choices=SITE_MODES, blank=True, null=True, default=None)

    INCREMENTS = (
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )
    increment = models.CharField(max_length=10, choices=INCREMENTS, default=None, null=True, blank=True)
    active = models.BooleanField(default=False)

    install_available = models.BooleanField(default=False)

    def __str__(self):
        return "{}-{}".format(str(self.user), str(self.service))