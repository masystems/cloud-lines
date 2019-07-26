from django.db import models
from django.contrib.auth.models import User
from breeder.models import Breeder
from breed.models import Breed
from account.models import AttachedService


class Pedigree(models.Model):
    class Meta:
        get_latest_by = "order_date"

    creator = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True)
    breeder = models.ForeignKey(Breeder, on_delete=models.SET_NULL, blank=True, null=True)
    current_owner = models.ForeignKey(Breeder, on_delete=models.SET_NULL, blank=True, null=True, related_name='owner', verbose_name='current owner')
    reg_no = models.CharField(max_length=100, blank=True, verbose_name='registration number')
    tag_no = models.CharField(max_length=100, blank=True, null=True, verbose_name='tag number')
    name = models.CharField(max_length=100, blank=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    date_of_registration = models.DateField(blank=True, null=True, verbose_name='date of registration')
    dob = models.DateField(blank=True, null=True, verbose_name='date of birth')
    dod = models.DateField(blank=True, null=True, verbose_name='date of death')

    GENDERS = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('castrated', 'Castrated'),
    )

    sex = models.CharField(max_length=10, choices=GENDERS, default=None, null=True)
    parent_father = models.ForeignKey('self', related_name='father', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='father')
    parent_mother = models.ForeignKey('self', related_name='mother', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='mother')
    breed_group = models.CharField(max_length=255, blank=True, null=True, verbose_name='breed group name')
    note = models.CharField(max_length=255, blank=True, verbose_name='Notes')

    # hidden
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reg_no


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'acc_{0}/{1}'.format(instance.account.id, filename)


class PedigreeImage(models.Model):
    reg_no = models.ForeignKey(Pedigree, related_name='images', on_delete=models.SET_NULL, blank=True, null=True)
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True)
    image = models.ImageField(upload_to=user_directory_path)
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return str(self.reg_no)


class PedigreeAttributes(models.Model):
    reg_no = models.OneToOneField(Pedigree, on_delete=models.CASCADE, primary_key=True, related_name='attribute')
    breed = models.ForeignKey(Breed, on_delete=models.CASCADE, blank=True, null=True, related_name='breed', verbose_name='breed')
    custom_fields = models.TextField(blank=True)

    def __str__(self):
        return str(self.reg_no)