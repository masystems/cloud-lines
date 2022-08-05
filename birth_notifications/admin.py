from django.contrib import admin
from .models import BirthNotification, BnChild, BnStripeAccount


admin.site.register(BirthNotification)
admin.site.register(BnChild)
admin.site.register(BnStripeAccount)