# Generated by Django 2.2.27 on 2022-11-09 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedigree', '0009_auto_20210718_1500'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedigree',
            name='paid',
            field=models.BooleanField(default=False),
        ),
    ]
