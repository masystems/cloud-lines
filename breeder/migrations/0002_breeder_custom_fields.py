# Generated by Django 2.1.10 on 2019-07-15 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('breeder', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='breeder',
            name='custom_fields',
            field=models.TextField(blank=True),
        ),
    ]
