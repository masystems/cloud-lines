# Generated by Django 2.1.10 on 2019-07-21 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedigree', '0003_auto_20190712_2014'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedigree',
            name='tag_no',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
