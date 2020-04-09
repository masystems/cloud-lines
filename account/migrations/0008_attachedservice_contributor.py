# Generated by Django 2.2.5 on 2019-10-22 20:09

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('account', '0007_attachedservice_domain'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachedservice',
            name='contributor',
            field=models.ManyToManyField(blank=True, related_name='contributors', to=settings.AUTH_USER_MODEL),
        ),
    ]
