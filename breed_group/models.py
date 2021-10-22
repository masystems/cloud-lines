from django.db import models
from pedigree.models import Pedigree
from breeder.models import Breeder
from breed.models import Breed
from account.models import AttachedService


class BreedGroup(models.Model):
    class Meta:
        get_latest_by = "state"
    STATES = (
        ('edited', 'Edited'),
        ('unapproved', 'Unapproved'),
        ('approved', 'Approved'),
    )
    state = models.CharField(max_length=10, choices=STATES, null=True, default='approved')
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True)
    breeder = models.ForeignKey(Breeder, on_delete=models.CASCADE, blank=True, null=True)
    breed = models.ForeignKey(Breed, on_delete=models.CASCADE, blank=True, null=True)
    group_name = models.CharField(max_length=100)
    group_id = models.CharField(max_length=100, blank=True, unique=True, verbose_name='Breed Group ID', help_text="Must be unique")
    group_members = models.ManyToManyField(Pedigree)
    date_added = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return self.group_id