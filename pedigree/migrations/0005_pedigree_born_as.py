# Generated by Django 2.2.11 on 2020-09-18 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedigree', '0004_auto_20200701_1924'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedigree',
            name='born_as',
            field=models.CharField(choices=[('single', 'Single'), ('twin', 'Twin'), ('triplet', 'Triplet'), ('quad', 'Quad')], default='single', help_text='Accepted formats: single, twin, triplet, quad', max_length=10, null=True),
        ),
    ]
