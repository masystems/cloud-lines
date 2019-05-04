from django.db import models


class Breeder(models.Model):

    prefix = models.CharField(max_length=100, blank=False)
    contact_name = models.CharField(max_length=100, blank=True)

    address = models.CharField(max_length=250, blank=True)
    phone_number1 = models.CharField(max_length=100, blank=True)
    phone_number2 = models.CharField(max_length=100, blank=True)
    email = models.CharField(max_length=100, blank=True)

    active = models.BooleanField(default=False)

    def __str__(self):
        return self.prefix