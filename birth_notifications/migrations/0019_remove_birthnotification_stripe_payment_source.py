# Generated by Django 2.2.27 on 2022-10-18 07:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('birth_notifications', '0018_birthnotification_paid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='birthnotification',
            name='stripe_payment_source',
        ),
    ]
