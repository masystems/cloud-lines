# Generated by Django 2.2.27 on 2022-10-18 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0021_auto_20221018_0731'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bnstripe',
            name='bn_child_cost_id',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='bnstripe',
            name='bn_cost_id',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='bnstripe',
            name='bn_stripe_product_id',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
