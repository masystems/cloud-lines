# Generated by Django 2.1.7 on 2019-04-26 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0008_auto_20190424_1801'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='priority',
            field=models.CharField(choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], default='low', max_length=10),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='status',
            field=models.CharField(choices=[('waiting_on_customer', 'Waiting on customer'), ('open', 'Open'), ('closed', 'Closed')], default='open', max_length=100),
        ),
    ]
