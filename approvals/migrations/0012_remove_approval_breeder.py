# Generated by Django 2.2.5 on 2019-10-24 20:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('approvals', '0011_auto_20191024_1948'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='approval',
            name='breeder',
        ),
    ]
