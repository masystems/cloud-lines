# Generated by Django 2.2.27 on 2022-06-22 21:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud_lines', '0008_bolton_stripe_price_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='bolton',
            name='test_stripe_price_id',
            field=models.CharField(blank=True, max_length=250),
        ),
    ]