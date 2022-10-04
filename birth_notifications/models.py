from django.db import models
from django.contrib.auth.models import User
from pedigree.models import Pedigree
from account.models import AttachedService, AttachedBolton


class BnChild(models.Model):
    tag_no = models.CharField(max_length=100, blank=True, verbose_name='Tag Number', help_text="Must be unique")
    # colour = models.CharField(max_length=100, blank=True, verbose_name='Colour', help_text="")
    STATUSES = (
        ('deceased', 'Deceased'),
        ('alive', 'Alive'),
        ('died_pre_reg', 'Died Pre Reg'),
    )

    status = models.CharField(max_length=10, choices=STATUSES, null=True, default='unknown',
                              help_text="Accepted formats: dead, alive, unknown", verbose_name="Status")

    GENDERS = (
        ('male', 'Male'),
        ('female', 'Female'),
    )

    sex = models.CharField(max_length=10, choices=GENDERS, null=True, default='unknown',
                           help_text="Accepted formats: male, female", verbose_name="Sex")

    comments = models.TextField(max_length=1000, blank=True, null=True, verbose_name="Comments",
                               help_text="Max 1000 characters")

    for_sale = models.BooleanField(null=True, default=False)

    pedigree = models.ForeignKey(Pedigree, related_name='registered_ped', on_delete=models.SET_NULL, blank=True, null=True)
    approved = models.BooleanField(default=False)


class BirthNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Account")
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Account")
    attached_bolton = models.ForeignKey(AttachedBolton, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Attached Bolton")
    mother = models.ForeignKey(Pedigree, related_name='bnmother', on_delete=models.SET_NULL, blank=True, null=True)
    father = models.ForeignKey(Pedigree, related_name='bnfather', on_delete=models.SET_NULL, blank=True, null=True)

    births = models.ManyToManyField(BnChild, related_name='births', blank=True)

    bn_number = models.CharField(max_length=255, blank=True, unique=True)
    dob = models.DateField(blank=True, null=True, verbose_name="Date Of Birth(s)")
    date_added = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(max_length=1000, blank=True, null=True, verbose_name="Comments", help_text="Max 1000 characters")

    stripe_payment_token = models.CharField(max_length=255, blank=True)
    stripe_payment_source = models.CharField(max_length=255, blank=True)

    complete = models.BooleanField(default=False)


class BnStripeAccount(models.Model):
    account = models.ForeignKey(AttachedService, on_delete=models.SET_NULL, blank=True, null=True,
                                verbose_name="BnN Stripe Account")
    attached_bolton = models.ForeignKey(AttachedBolton, on_delete=models.SET_NULL, blank=True, null=True,
                                        verbose_name="Attached Bolton")
    stripe_acct_id = models.CharField(max_length=255, blank=True, unique=True)
    stripe_product_id = models.CharField(max_length=255, blank=True, unique=True)
    account_name = models.CharField(max_length=255, blank=True)
    bn_cost = models.IntegerField(default=0, blank=True)
    bn_child_cost = models.IntegerField(default=0, blank=True)
    ped_cost = models.IntegerField(default=0, blank=True)