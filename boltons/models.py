from django.db import models
from cloud_lines.models import Bolton
from pedigree.models import Pedigree
from account.models import AttachedService


class BirthNotification(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Account")
    mother = models.ForeignKey(Pedigree, related_name='bnmother', on_delete=models.SET_NULL, blank=True, null=True)
    father = models.ForeignKey(Pedigree, related_name='bnfather', on_delete=models.SET_NULL, blank=True, null=True)
    SERVICE_METHODS = (
        ('natural_service', 'Natual Service'),
        ('embryo_implant', 'Embryo Implant'),
        ('ai', 'Artificial Insemination'),
    )

    service_method = models.CharField(max_length=10, choices=SERVICE_METHODS, null=True, default='unknown', verbose_name="Status")

    living_males = models.IntegerField(default=0, null=True)
    living_females = models.IntegerField(default=0, null=True)
    deceased_males = models.IntegerField(default=0, null=True)
    deceased_females = models.IntegerField(default=0, null=True)

    comments = models.TextField(max_length=1000, blank=True, null=True, verbose_name="Comments", help_text="Max 1000 characters")