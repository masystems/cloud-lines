# Generated by Django 2.2.11 on 2020-10-06 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud_lines', '0006_bolton'),
        ('account', '0005_attachedservice_organisation_or_society_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachedservice',
            name='boltons',
            field=models.ManyToManyField(blank=True, related_name='boltons', to='cloud_lines.Bolton'),
        ),
    ]
