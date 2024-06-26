# Generated by Django 2.2.24 on 2022-04-16 21:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('birth_notifications', '0002_auto_20220409_2042'),
    ]

    operations = [
        migrations.CreateModel(
            name='BnChild',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reg_no', models.CharField(blank=True, help_text='Must be unique', max_length=100, unique=True, verbose_name='Registration Number')),
                ('status', models.CharField(choices=[('dead', 'Dead'), ('alive', 'Alive'), ('unknown', 'Unknown')], default='unknown', help_text='Accepted formats: dead, alive, unknown', max_length=10, null=True, verbose_name='Status')),
                ('sex', models.CharField(choices=[('male', 'Male'), ('female', 'Female')], default='unknown', help_text='Accepted formats: male, female', max_length=10, null=True, verbose_name='Sex')),
            ],
        ),
        migrations.RemoveField(
            model_name='birthnotification',
            name='deceased_females',
        ),
        migrations.RemoveField(
            model_name='birthnotification',
            name='deceased_males',
        ),
        migrations.RemoveField(
            model_name='birthnotification',
            name='living_females',
        ),
        migrations.RemoveField(
            model_name='birthnotification',
            name='living_males',
        ),
        migrations.RemoveField(
            model_name='birthnotification',
            name='service_method',
        ),
        migrations.AddField(
            model_name='birthnotification',
            name='births',
            field=models.ManyToManyField(blank=True, related_name='births', to='birth_notifications.BnChild'),
        ),
    ]
