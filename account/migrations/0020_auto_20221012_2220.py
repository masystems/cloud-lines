# Generated by Django 2.2.27 on 2022-10-12 22:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0019_auto_20221012_2148'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bnstripe',
            name='bn_child_cost_id',
            field=models.CharField(blank=True, max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='bnstripe',
            name='bn_cost_id',
            field=models.CharField(blank=True, max_length=255, unique=True),
        ),
    ]
