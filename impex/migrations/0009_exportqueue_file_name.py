# Generated by Django 2.2.24 on 2021-08-29 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('impex', '0008_auto_20210829_1733'),
    ]

    operations = [
        migrations.AddField(
            model_name='exportqueue',
            name='file_name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]