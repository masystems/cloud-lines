# Generated by Django 2.2.11 on 2021-06-09 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metrics', '0009_datavalidatorqueue'),
    ]

    operations = [
        migrations.AddField(
            model_name='datavalidatorqueue',
            name='result',
            field=models.TextField(blank=True),
        ),
    ]
