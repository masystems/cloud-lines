from django.db import models
from account.models import AttachedService


def user_directory_path(instance, filename):
    return 'acc_{0}_{1}/{2}'.format(instance.account.id, instance.account.domain.replace('https://', ''), filename)


class DatabaseUpload(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True)
    database = models.ImageField(upload_to=user_directory_path)
    FILE_TYPES = (
        ('.csv', '.csv'),
    )
    file_type = models.CharField(max_length=5, choices=FILE_TYPES, default=None, null=True)

    def __str__(self):
        return str(self.database)