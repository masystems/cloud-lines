# Generated by Django 2.2.27 on 2022-08-23 23:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('birth_notifications', '0010_auto_20220810_2041'),
    ]

    operations = [
        migrations.AddField(
            model_name='bnstripeaccount',
            name='bn_child_cost',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='bnstripeaccount',
            name='bn_cost',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='bnstripeaccount',
            name='ped_cost',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]