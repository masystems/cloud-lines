# Generated by Django 2.1.7 on 2019-05-10 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud_lines', '0008_service_icon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='icon',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
