# Generated by Django 3.2 on 2023-06-22 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('birth_notifications', '0020_birthnotification_breeder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='birthnotification',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='bnchild',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='bnchild',
            name='status',
            field=models.CharField(choices=[('deceased', 'Deceased'), ('alive', 'Alive'), ('died_pre_reg', 'Died Pre Reg')], default='unknown', help_text='Accepted formats: dead, alive, unknown', max_length=12, null=True, verbose_name='Status'),
        ),
    ]