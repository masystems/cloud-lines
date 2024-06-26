from django.db import models
from django.contrib.auth.models import User
from account.models import AttachedService


def user_directory_path(instance, filename):
    return 'acc_{0}_{1}/{2}'.format(instance.account.id, instance.account.domain.replace('https://', ''), filename)


class DatabaseUpload(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.CASCADE)
    header = models.TextField(blank=False, null=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    errors = models.TextField(default={'missing': [], 'invalid': []})
    total_lines = models.IntegerField(null=True)

    def __str__(self):
        return str(self.account)


class FileSlice(models.Model):
    file_slice = models.TextField(blank=True)
    database_upload = models.ForeignKey(DatabaseUpload, on_delete=models.CASCADE, related_name='file_slice')
    FILE_TYPES = (
        ('.csv', '.csv'),
    )
    file_type = models.CharField(max_length=5, choices=FILE_TYPES, default='.csv', null=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return str(self.file_slice)


class ExportQueue(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file_name = models.CharField(max_length=255, blank=True)
    complete = models.BooleanField(default=False)
    download_url = models.CharField(max_length=255, blank=True)
    created = models.DateTimeField(auto_now_add=True)