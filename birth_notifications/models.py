from django.db import models
from django.contrib.auth.models import User
from pedigree.models import Pedigree
from account.models import AttachedService, AttachedBolton


class BirthNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Account")
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Account")
    attached_bolton = models.ForeignKey(AttachedBolton, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Attached Bolton")
    mother = models.ForeignKey(Pedigree, related_name='bnmother', on_delete=models.SET_NULL, blank=True, null=True)
    father = models.ForeignKey(Pedigree, related_name='bnfather', on_delete=models.SET_NULL, blank=True, null=True)


    living_males = models.IntegerField(default=0, null=True)
    living_females = models.IntegerField(default=0, null=True)
    deceased_males = models.IntegerField(default=0, null=True)
    deceased_females = models.IntegerField(default=0, null=True)

    SERVICE_METHODS = (
        ('natural_service', 'Natual Service'),
        ('embryo_implant', 'Embryo Implant'),
        ('ai', 'Artificial Insemination'),
    )

    service_method = models.CharField(max_length=250, choices=SERVICE_METHODS, null=True, default='unknown',
                                      verbose_name="Status")

    bn_number = models.CharField(max_length=255, blank=True, unique=True)

    date_added = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(max_length=1000, blank=True, null=True, verbose_name="Comments", help_text="Max 1000 characters")