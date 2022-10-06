# Generated by Django 2.2.27 on 2022-10-06 22:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0016_auto_20220921_2205'),
    ]

    operations = [
        migrations.CreateModel(
            name='StripeAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_acct_id', models.CharField(blank=True, max_length=255, unique=True)),
                ('stripe_product_id', models.CharField(blank=True, max_length=255, unique=True)),
                ('account_name', models.CharField(blank=True, max_length=255)),
                ('bn_cost', models.IntegerField(blank=True, default=0)),
                ('bn_child_cost', models.IntegerField(blank=True, default=0)),
                ('ped_cost', models.IntegerField(blank=True, default=0)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.AttachedService', verbose_name='BnN Stripe Account')),
                ('attached_bolton', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.AttachedBolton', verbose_name='Attached Bolton')),
            ],
        ),
    ]
