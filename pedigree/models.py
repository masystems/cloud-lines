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
    breeder = models.ForeignKey(Breeder, on_delete=models.SET_NULL, blank=True, null=True, help_text="Often the same as Current Owner")
    current_owner = models.ForeignKey(Breeder, on_delete=models.SET_NULL, blank=True, null=True, related_name='owner', verbose_name='current owner', help_text="Often the same as Breeder")
    reg_no = models.CharField(max_length=100, blank=True, unique=True, verbose_name='registration number', help_text="Must be unique")
    tag_no = models.CharField(max_length=100, blank=True, null=True, verbose_name='tag number')
    name = models.CharField(max_length=100, blank=True)
    description = models.TextField(max_length=1000, blank=True, null=True, help_text="Max 1000 characters")
    date_of_registration = models.DateField(blank=True, null=True, verbose_name='date of registration', help_text="Date formats: 1984/09/31, 84/09/31, 31/09/1984, 31/09/84, 1984-09-31, 84-09-31, 31-09-1984, 31-09-84")
    dob = models.DateField(blank=True, null=True, verbose_name='date of birth', help_text="Date formats: 1984/09/31, 84/09/31, 31/09/1984, 31/09/84, 1984-09-31, 84-09-31, 31-09-1984, 31-09-84")
    dod = models.DateField(blank=True, null=True, verbose_name='date of death', help_text="Date formats: 1984/09/31, 84/09/31, 31/09/1984, 31/09/84, 1984-09-31, 84-09-31, 31-09-1984, 31-09-84")

    GENDERS = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('castrated', 'Castrated'),
    )

    sex = models.CharField(max_length=10, choices=GENDERS, null=True, default='female', help_text="Accepted formats: male, female, castrated")
    parent_father = models.ForeignKey('self', related_name='father', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='father', help_text="This should be the parents registration number.")
    parent_father_notes = models.CharField(max_length=500, blank=True, verbose_name='Father Notes', help_text="Max 500 characters")
    parent_mother = models.ForeignKey('self', related_name='mother', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='mother', help_text="This should be the parents registration number.")
    parent_mother_notes = models.CharField(max_length=500, blank=True, verbose_name='Mother Notes', help_text="Max 500 characters")
    breed_group = models.CharField(max_length=255, blank=True, null=True, verbose_name='breed group name')

    # hidden
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reg_no


def user_directory_path(instance, filename):
    return 'acc_{0}_{1}/{2}'.format(instance.account.id, instance.account.domain.replace('https://', ''), filename)


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