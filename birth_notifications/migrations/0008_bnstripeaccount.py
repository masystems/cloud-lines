# Generated by Django 2.2.27 on 2022-07-16 14:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0014_attachedbolton_stripe_acct_id'),
        ('birth_notifications', '0007_auto_20220621_2122'),
    ]

    operations = [
        migrations.CreateModel(
            name='BnStripeAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_acct_id', models.CharField(blank=True, max_length=255, unique=True)),
                ('account_name', models.CharField(blank=True, max_length=255, unique=True)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.AttachedService', verbose_name='BnN Stripe Account')),
                ('attached_bolton', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.AttachedBolton', verbose_name='Attached Bolton')),
            ],
        ),
    ]
