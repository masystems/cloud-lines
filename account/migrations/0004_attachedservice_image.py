# Generated by Django 2.2.11 on 2020-07-13 22:16

import account.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_attachedservice_pedigree_columns'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachedservice',
            name='image',
            field=models.ImageField(blank=True, upload_to=account.models.user_directory_path),
        ),
    ]
