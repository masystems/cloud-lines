# Generated by Django 2.1.10 on 2019-07-27 20:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pedigree', '0006_auto_20190727_1234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedigree',
            name='breeder',
            field=models.ForeignKey(blank=True, help_text='Often the same as Current Owner', null=True, on_delete=django.db.models.deletion.SET_NULL, to='breeder.Breeder'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='current_owner',
            field=models.ForeignKey(blank=True, help_text='Often the same as Breeder', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owner', to='breeder.Breeder', verbose_name='current owner'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='date_of_registration',
            field=models.DateField(blank=True, help_text='Date formats: 1984/09/31, 84/09/31, 31/09/1984, 31/09/84, 1984-09-31, 84-09-31, 31-09-1984, 31-09-84', null=True, verbose_name='date of registration'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='description',
            field=models.TextField(blank=True, help_text='Max 1000 characters', max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='dob',
            field=models.DateField(blank=True, help_text='Date formats: 1984/09/31, 84/09/31, 31/09/1984, 31/09/84, 1984-09-31, 84-09-31, 31-09-1984, 31-09-84', null=True, verbose_name='date of birth'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='dod',
            field=models.DateField(blank=True, help_text='Date formats: 1984/09/31, 84/09/31, 31/09/1984, 31/09/84, 1984-09-31, 84-09-31, 31-09-1984, 31-09-84', null=True, verbose_name='date of death'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='note',
            field=models.CharField(blank=True, help_text='Max 500 characters', max_length=500, verbose_name='Notes'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='parent_father',
            field=models.ForeignKey(blank=True, help_text='This should be the parents registration number.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='father', to='pedigree.Pedigree', verbose_name='father'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='parent_mother',
            field=models.ForeignKey(blank=True, help_text='This should be the parents registration number.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mother', to='pedigree.Pedigree', verbose_name='mother'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='reg_no',
            field=models.CharField(blank=True, help_text='Must be unique', max_length=100, verbose_name='registration number'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='sex',
            field=models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('castrated', 'Castrated')], default=None, help_text='Accepted formats: male, female, castrated', max_length=10, null=True),
        ),
    ]
