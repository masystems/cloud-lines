from django.contrib import admin
from .models import BirthNotification, BnChild


admin.site.register(BirthNotification)
admin.site.register(BnChild)