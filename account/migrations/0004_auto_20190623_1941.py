# Generated by Django 2.1.9 on 2019-06-23 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_attachedservice_subscription_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachedservice',
            name='subscription_id',
            field=models.CharField(blank=True, max_length=250),
        ),
    ]
