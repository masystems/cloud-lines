# Generated by Django 2.2.24 on 2021-08-02 08:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metrics', '0010_datavalidatorqueue_result'),
    ]

    operations = [
        migrations.AddField(
            model_name='studadvisorqueue',
            name='mk_threshold',
            field=models.DecimalField(blank=True, decimal_places=4, default=0.0, help_text='This value is the mean kinship threshold of the breed of the mother at the time this stud advice was created.', max_digits=6, null=True, verbose_name='Mean Kinship threshold'),
        ),
    ]
