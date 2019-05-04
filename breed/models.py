from django.db import models


class Breed(models.Model):
    breed_name = models.CharField(max_length=100)
    image = models.ImageField(blank=True)
    description = models.TextField(max_length=1000, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.breed_name
