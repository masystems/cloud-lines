# Generated by Django 2.2 on 2019-05-03 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0010_auto_20190503_1305'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='priority',
            field=models.CharField(choices=[('medium', 'Medium'), ('low', 'Low'), ('high', 'High')], default='low', max_length=10),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='status',
            field=models.CharField(choices=[('closed', 'Closed'), ('open', 'Open'), ('waiting_on_customer', 'Waiting on customer')], default='open', max_length=100),
        ),
    ]
