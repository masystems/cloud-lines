# Generated by Django 2.2.27 on 2022-10-04 22:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('birth_notifications', '0015_bnchild_for_sale'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bnstripeaccount',
            name='account_name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
