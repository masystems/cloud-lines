from django.db import models
from account.models import AttachedService


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'acc_{0}/{1}'.format(instance.account.id, filename)


class DatabaseUpload(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True)
    database = models.ImageField(upload_to=user_directory_path)
    FILE_TYPES = (
        ('.csv', '.csv'),
    )
    file_type = models.CharField(max_length=5, choices=FILE_TYPES, default=None, null=True)

    def __str__(self):
        return str(self.database)