# Generated by Django 2.1.10 on 2019-08-02 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_auto_20190721_1838'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachedservice',
            name='domain',
            field=models.CharField(blank=True, max_length=250),
        ),
    ]
