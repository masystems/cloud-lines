# Generated by Django 2.2.24 on 2021-07-18 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedigree', '0008_auto_20210716_1031'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedigree',
            name='sex',
            field=models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('castrated', 'Castrated'), ('unknown', 'Unknown')], default='unknown', help_text='Accepted formats: male, female, castrated, unknown', max_length=10, null=True, verbose_name='Sex'),
        ),
    ]