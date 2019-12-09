from django.db import models
from account.models import AttachedService


class CoiLastRun(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True,
                                verbose_name="Account")
    last_run = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.account)


class MeanKinshipLastRun(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True,
                                verbose_name="Account")
    last_run = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.account)
