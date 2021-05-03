from django.db import models
from account.models import AttachedService
from django.contrib.auth.models import User
from pedigree.models import Pedigree


class CoiLastRun(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.CASCADE, blank=True, null=True,
                                verbose_name="Account")
    last_run = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.account)


class MeanKinshipLastRun(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.CASCADE, blank=True, null=True,
                                verbose_name="Account")
    last_run = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.account)


class KinshipQueue(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.CASCADE, verbose_name="Account")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    mother = models.ForeignKey(Pedigree, on_delete=models.CASCADE, blank=True, null=True, related_name="kmotherq", verbose_name="Mother")
    father = models.ForeignKey(Pedigree, on_delete=models.CASCADE, blank=True, null=True, related_name="kfatherq", verbose_name="Father")
    file = models.CharField(max_length=250)
    email_sent = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)


class StudAdvisorQueue(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.CASCADE, verbose_name="Account")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    mother = models.ForeignKey(Pedigree, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Mother")
    file = models.CharField(max_length=250)
    email_sent = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
