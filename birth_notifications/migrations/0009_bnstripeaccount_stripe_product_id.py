# Generated by Django 2.2.27 on 2022-07-27 21:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('birth_notifications', '0008_bnstripeaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='bnstripeaccount',
            name='stripe_product_id',
            field=models.CharField(blank=True, max_length=255, unique=True),
        ),
    ]