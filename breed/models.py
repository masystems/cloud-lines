from django.db import models
from account.models import AttachedService


class Breed(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True)
    breed_name = models.CharField(max_length=100)
    image = models.ImageField(blank=True)
    description = models.TextField(max_length=2000, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.breed_name
