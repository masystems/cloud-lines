# Generated by Django 2.2.24 on 2021-07-16 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('breeder', '0005_auto_20210409_1013'),
    ]

    operations = [
        migrations.AlterField(
            model_name='breeder',
            name='breeding_prefix',
            field=models.CharField(max_length=100),
        ),
    ]
