from django.db import models
from account.models import AttachedService


def user_directory_path(instance, filename):
    return 'acc_{0}_{1}/{2}'.format(instance.account.id, instance.account.domain.replace('https://', ''), filename)


class Breed(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True)
    breed_name = models.CharField(max_length=100)
    image = models.ImageField(blank=True, upload_to=user_directory_path)
    breed_description = models.TextField(max_length=2000, blank=True)
    custom_fields = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    mk_a = models.DecimalField(max_digits=6, decimal_places=4, verbose_name='Mean Kinship Group A', blank=True)
    mk_b = models.DecimalField(max_digits=6, decimal_places=4, verbose_name='Mean Kinship Group B', blank=True)
    mk_c = models.DecimalField(max_digits=6, decimal_places=4, verbose_name='Mean Kinship Group C', blank=True)
    mk_d = models.DecimalField(max_digits=6, decimal_places=4, verbose_name='Mean Kinship Group D', blank=True)

    def __str__(self):
        return self.breed_name
