# Generated by Django 2.2.27 on 2022-09-06 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('birth_notifications', '0013_auto_20220906_2138'),
    ]

    operations = [
        migrations.AddField(
            model_name='birthnotification',
            name='stripe_payment_source',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
