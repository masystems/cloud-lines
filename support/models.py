from django.db import models
from django.contrib.auth.models import User
from account.models import AttachedService


class Ticket(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    date_time = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=250, blank=False)

    PRIORITIES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    priority = models.CharField(max_length=10, choices=PRIORITIES, default='low', null=False)

    description = models.TextField(max_length=1000, blank=False)

    STATUS_TYPES = (
        ('open', 'Open'),
        ('waiting_on_customer', 'Waiting on customer'),
        ('closed', 'Closed'),
    )
    status = models.CharField(max_length=100, choices=STATUS_TYPES, default='open', null=False)

    def __str__(self):
        return self.subject