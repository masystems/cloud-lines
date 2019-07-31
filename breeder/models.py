from django.db import models
from account.models import AttachedService


class Breeder(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True)
    breeding_prefix = models.CharField(max_length=100, blank=False, help_text="Must be unique")
    contact_name = models.CharField(max_length=100, blank=True, help_text="The primary contact for the breeder/owner")

    address = models.CharField(max_length=250, blank=True)
    phone_number1 = models.CharField(max_length=100, blank=True)
    phone_number2 = models.CharField(max_length=100, blank=True)
    email = models.CharField(max_length=100, blank=True)
    custom_fields = models.TextField(blank=True)

    active = models.BooleanField(default=False, help_text="Is the breeder currently active?")

    def __str__(self):
        return self.breeding_prefix