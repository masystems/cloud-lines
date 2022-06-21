# Generated by Django 2.2.24 on 2022-04-09 20:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0013_auto_20211210_1550'),
        ('pedigree', '0009_auto_20210718_1500'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BirthNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bn_number', models.CharField(blank=True, max_length=255, unique=True)),
                ('service_method', models.CharField(choices=[('natural_service', 'Natual Service'), ('embryo_implant', 'Embryo Implant'), ('ai', 'Artificial Insemination')], default='unknown', max_length=10, null=True, verbose_name='Status')),
                ('living_males', models.IntegerField(default=0, null=True)),
                ('living_females', models.IntegerField(default=0, null=True)),
                ('deceased_males', models.IntegerField(default=0, null=True)),
                ('deceased_females', models.IntegerField(default=0, null=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('comments', models.TextField(blank=True, help_text='Max 1000 characters', max_length=1000, null=True, verbose_name='Comments')),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.AttachedService', verbose_name='Account')),
                ('attached_bolton', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.AttachedBolton', verbose_name='Attached Bolton')),
                ('father', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bnfather', to='pedigree.Pedigree')),
                ('mother', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bnmother', to='pedigree.Pedigree')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Account')),
            ],
        ),
    ]
