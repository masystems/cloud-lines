# Generated by Django 2.1.7 on 2019-04-15 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedigree', '0012_auto_20190414_2206'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedigree',
            name='sex',
            field=models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('castrated', 'Castrated')], default=None, max_length=10, null=True),
        ),
    ]
