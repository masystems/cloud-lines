# Generated by Django 2.1.10 on 2019-07-12 20:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_auto_20190623_1941'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachedservice',
            name='custom_fields',
            field=models.TextField(blank=True),
        ),
    ]
