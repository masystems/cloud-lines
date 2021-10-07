from django.db import models
from django.contrib.auth.models import User
from cloud_lines.models import Service
from cloud_lines.models import Bolton
from json import dumps


def user_directory_path(instance, filename):
    return 'acc_{0}_{1}/{2}'.format(instance.id, instance.domain.replace('https://', ''), filename)


class UserDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user')
    phone = models.CharField(max_length=15, blank=False)
    stripe_id = models.CharField(max_length=50, blank=True)
    current_service = models.ForeignKey('AttachedService', on_delete=models.SET_NULL, null=True, blank=True)
    graphs = models.TextField(default=dumps({'total_line': True, 'total_bar': True, 'living_bar': False}), verbose_name="Dashboard Graphs")

    def __str__(self):
        return str(self.user)


class AttachedService(models.Model):
    user = models.ForeignKey(UserDetail, on_delete=models.CASCADE, related_name='attached_service', null=True, blank=True)
    admin_users = models.ManyToManyField(User, related_name='admin_users', blank=True)
    contributors = models.ManyToManyField(User, related_name='contributors', blank=True)
    read_only_users = models.ManyToManyField(User, related_name='read_only_users', blank=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    boltons = models.ManyToManyField(Bolton, related_name='boltons', blank=True)
    domain = models.CharField(max_length=250, blank=True)
    organisation_or_society_name = models.CharField(max_length=250, blank=True)
    image = models.ImageField(upload_to=user_directory_path, blank=True)
    animal_type = models.CharField(max_length=250)
    custom_fields = models.TextField(blank=True)
    pedigree_columns = models.CharField(blank=False, max_length=500, default="reg_no,mean_kinship,name,dob,status,breed,sex")
    mother_title = models.CharField(max_length=250, default='Mother')
    father_title = models.CharField(max_length=250, default='Father')
    coi_timeout = models.IntegerField(default=60)
    mean_kinship_timeout = models.IntegerField(default=60)
    metrics = models.BooleanField(default=False)

    SITE_MODES = (
        ('mammal', 'Mammal'),
        ('poultry', 'Poultry'),
    )
    site_mode = models.CharField(max_length=13, choices=SITE_MODES, blank=True, null=True, default='poultry')

    INCREMENTS = (
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )
    increment = models.CharField(max_length=10, choices=INCREMENTS, default=None, null=True, blank=True)
    active = models.BooleanField(default=False)
    subscription_id = models.CharField(max_length=250, blank=True)

    install_available = models.BooleanField(default=False)

    def __str__(self):
        return "{}-{}".format(str(self.user), str(self.service))