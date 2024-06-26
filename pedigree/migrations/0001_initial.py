# Generated by Django 2.2.11 on 2020-04-16 14:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import pedigree.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0001_initial'),
        ('breed', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('breeder', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pedigree',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('edited', 'Edited'), ('unapproved', 'Unapproved'), ('approved', 'Approved')], default='approved', max_length=10, null=True)),
                ('reg_no', models.CharField(blank=True, help_text='Must be unique', max_length=100, verbose_name='registration number')),
                ('tag_no', models.CharField(blank=True, max_length=100, null=True, verbose_name='tag number')),
                ('name', models.CharField(blank=True, max_length=100, verbose_name='Name')),
                ('description', models.TextField(blank=True, help_text='Max 1000 characters', max_length=1000, null=True, verbose_name='Description')),
                ('date_of_registration', models.DateField(blank=True, help_text='Date formats: 1984/09/31, 84/09/31, 31/09/1984, 31/09/84, 1984-09-31, 84-09-31, 31-09-1984, 31-09-84', null=True, verbose_name='date of registration')),
                ('dob', models.DateField(blank=True, help_text='Date formats: 1984/09/31, 84/09/31, 31/09/1984, 31/09/84, 1984-09-31, 84-09-31, 31-09-1984, 31-09-84', null=True, verbose_name='date of birth')),
                ('dod', models.DateField(blank=True, help_text='Date formats: 1984/09/31, 84/09/31, 31/09/1984, 31/09/84, 1984-09-31, 84-09-31, 31-09-1984, 31-09-84', null=True, verbose_name='date of death')),
                ('status', models.CharField(choices=[('dead', 'Dead'), ('alive', 'Alive'), ('unknown', 'Unknown')], default='unknown', help_text='Accepted formats: dead, alive, unknown', max_length=10, null=True)),
                ('sex', models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('castrated', 'Castrated')], default='female', help_text='Accepted formats: male, female, castrated', max_length=10, null=True)),
                ('parent_father_notes', models.CharField(blank=True, help_text='Max 500 characters', max_length=500, null=True, verbose_name='Father Notes')),
                ('parent_mother_notes', models.CharField(blank=True, help_text='Max 500 characters', max_length=500, null=True, verbose_name='Mother Notes')),
                ('breed_group', models.CharField(blank=True, max_length=255, null=True, verbose_name='Breed group name')),
                ('custom_fields', models.TextField(blank=True)),
                ('coi', models.DecimalField(blank=True, decimal_places=4, default=0, max_digits=5)),
                ('mean_kinship', models.DecimalField(blank=True, decimal_places=4, default=0, max_digits=5)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.AttachedService', verbose_name='Account')),
                ('breed', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='breed', to='breed.Breed')),
                ('breeder', models.ForeignKey(blank=True, help_text='Often the same as Current Owner', null=True, on_delete=django.db.models.deletion.SET_NULL, to='breeder.Breeder', verbose_name='Breeder')),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Creator')),
                ('current_owner', models.ForeignKey(blank=True, help_text='Often the same as Breeder', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owner', to='breeder.Breeder', verbose_name='current owner')),
                ('parent_father', models.ForeignKey(blank=True, help_text='This should be the parents registration number.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='father', to='pedigree.Pedigree', verbose_name='father')),
                ('parent_mother', models.ForeignKey(blank=True, help_text='This should be the parents registration number.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mother', to='pedigree.Pedigree', verbose_name='mother')),
            ],
            options={
                'get_latest_by': 'order_date',
            },
        ),
        migrations.CreateModel(
            name='PedigreeImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('edited', 'Edited'), ('unapproved', 'Unapproved'), ('approved', 'Approved')], default='approved', max_length=10, null=True)),
                ('image', models.ImageField(upload_to=pedigree.models.user_directory_path)),
                ('title', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True, max_length=500)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.AttachedService')),
                ('reg_no', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='images', to='pedigree.Pedigree')),
            ],
        ),
    ]
