# Generated by Django 3.2 on 2023-06-22 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_auto_20211027_2210'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportqueue',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
