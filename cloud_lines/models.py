from django.db import models


class Service(models.Model):
    ordering = models.IntegerField()
    icon = models.CharField(max_length=500, blank=True)
    service_name = models.CharField(max_length=50)
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

    def __str__(self):
        return self.service_name

    class Meta:
        ordering = ['ordering']


class Page(models.Model):
    title = models.CharField(max_length=50)
    sub_title = models.CharField(max_length=150)
    body = models.TextField()

    def __str__(self):
        return self.title


class Faq(models.Model):
    question = models.CharField(max_length=250)
    answer = models.TextField()

    def __str__(self):
        return self.question