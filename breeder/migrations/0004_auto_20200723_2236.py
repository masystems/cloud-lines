# Generated by Django 2.2.11 on 2020-07-23 22:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('breeder', '0003_auto_20200629_2004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='breeder',
            name='breeding_prefix',
            field=models.CharField(help_text='Must be unique', max_length=100, unique=True),
        ),
    ]