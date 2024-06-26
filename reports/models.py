from django.db import models
from django.contrib.auth.models import User
from account.models import AttachedService


class ReportQueue(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    report_name = models.CharField(max_length=255, blank=True)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=255, blank=True)
    complete = models.BooleanField(default=False)
    download_url = models.CharField(max_length=255, blank=True)
    created = models.DateTimeField(auto_now_add=True)