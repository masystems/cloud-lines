# Generated by Django 2.2.11 on 2021-06-01 18:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metrics', '0007_kinshipqueue'),
    ]

    operations = [
        migrations.AddField(
            model_name='kinshipqueue',
            name='result',
            field=models.CharField(blank=True, max_length=250),
        ),
    ]
