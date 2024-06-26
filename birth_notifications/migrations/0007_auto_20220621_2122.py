# Generated by Django 2.2.27 on 2022-06-21 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('birth_notifications', '0006_birthnotification_complete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bnchild',
            name='status',
            field=models.CharField(choices=[('deceased', 'Deceased'), ('alive', 'Alive'), ('died_pre_reg', 'Died Pre Reg')], default='unknown', help_text='Accepted formats: dead, alive, unknown', max_length=10, null=True, verbose_name='Status'),
        ),
    ]
