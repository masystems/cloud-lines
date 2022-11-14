# Generated by Django 2.2.27 on 2022-11-11 23:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0025_attachedservice_pedigree_charging'),
        ('birth_notifications', '0019_remove_birthnotification_stripe_payment_source'),
    ]

    operations = [
        migrations.CreateModel(
            name='BnSettings',
            fields=[
                ('stripeaccount_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='account.StripeAccount')),
                ('charging', models.BooleanField(default=False)),
            ],
            bases=('account.stripeaccount',),
        ),
    ]
