from django.db import models
from cloud_lines.models import Bolton
from pedigree.models import Pedigree


class BirthNotification(models.Model):
    pedigree = models.ForeignKey(Pedigree, related_name='birth_notification', on_delete=models.SET_NULL, blank=True, null=True)