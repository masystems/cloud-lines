from django.db import models
from django.contrib.auth.models import User


class Service(models.Model):
    ordering = models.IntegerField()
    active = models.BooleanField(default=True)
    icon = models.CharField(max_length=500, blank=True)
    image = models.FileField(blank=True)
    service_name = models.CharField(max_length=50, unique=True)
    admin_users = models.IntegerField()
    read_only_users = models.IntegerField()
    number_of_animals = models.IntegerField()
    multi_breed = models.BooleanField()
    support = models.BooleanField()
    support_cost_per_year = models.DecimalField(max_digits=5, decimal_places=2)
    price_per_month = models.DecimalField(max_digits=5, decimal_places=2)
    price_per_year = models.DecimalField(max_digits=5, decimal_places=2)
    total_price_per_year = models.DecimalField(max_digits=6, decimal_places=2)
    service_description = models.TextField()

    service_id = models.CharField(max_length=100, blank=True)
    monthly_id = models.CharField(max_length=100, blank=True)
    yearly_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.service_name

    class Meta:
        ordering = ['ordering']


class Page(models.Model):
    title = models.CharField(max_length=50, unique=True,)
    sub_title = models.CharField(max_length=150, blank=True)
    body = models.TextField()
    image = models.ImageField(blank=True)

    def __str__(self):
        return self.title


class Faq(models.Model):
    question = models.CharField(max_length=250)
    answer = models.TextField()

    def __str__(self):
        return self.question


class Contact(models.Model):
    name = models.CharField(max_length=250)
    email = models.CharField(max_length=250)
    phone = models.CharField(max_length=50, blank=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, blank=True, null=True)
    subject = models.CharField(max_length=250)
    message = models.TextField()

    def __str__(self):
        return self.name


class Testimonial(models.Model):
    name = models.CharField(max_length=250)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, blank=True, null=True)
    body = models.TextField()

    def __str__(self):
        return str(self.name)


class LargeTierQueue(models.Model):
    from account.models import UserDetail, AttachedService
    subdomain = models.CharField(max_length=255, blank=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='luser')
    user_detail = models.ForeignKey(UserDetail, on_delete=models.CASCADE, null=True, related_name='user_detail')
    attached_service = models.ForeignKey(AttachedService, on_delete=models.CASCADE, null=True, related_name='lattached_service')

    BUILD_STATE = (
        ('waiting', 'Waiting'),
        ('building', 'Building'),
        ('complete', 'Complete'),
    )
    build_state = models.CharField(max_length=20, choices=BUILD_STATE, default='waiting')
    build_status = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return str(self.subdomain)
