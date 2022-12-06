from django.db import models
from django.utils.crypto import get_random_string

from account.models import AttachedService

class Membership(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.CASCADE, related_name='attached_service', null=True, blank=True)
    token = models.CharField(max_length=250, blank=True)

    def get_or_create_token(self):
        if self.token in ['', None]:
            self.create_new_token()
        return self.token

    def create_new_token(self):
        self.token = get_random_string(length=32)
        self.save()
        return self.token