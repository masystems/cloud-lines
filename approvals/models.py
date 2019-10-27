from django.db import models
from django.contrib.auth.models import User
from account.models import AttachedService
from pedigree.models import Pedigree
from breeder.models import Breeder
from breed_group.models import BreedGroup


class Approval(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True,
                                verbose_name="account")
    TYPES = (
        ('edit', 'edit'),
        ('new', 'New'),
    )
    type = models.CharField(max_length=10, choices=TYPES, null=True, default='new')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='editor')
    pedigree = models.ForeignKey(Pedigree, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="pedigree")
    breed_group = models.ForeignKey(BreedGroup, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="breed_group")

    message = models.TextField(blank=True)
    data = models.TextField(blank=True)

    date_created = models.DateTimeField(auto_now_add=True)
