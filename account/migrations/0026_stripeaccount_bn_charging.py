# Generated by Django 2.2.27 on 2022-11-13 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0025_attachedservice_pedigree_charging'),
    ]

    operations = [
        migrations.AddField(
            model_name='stripeaccount',
            name='bn_charging',
            field=models.BooleanField(default=False),
        ),
    ]
