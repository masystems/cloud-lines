# Generated by Django 2.2.11 on 2021-03-30 16:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pedigree', '0005_pedigree_born_as'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedigree',
            name='born_as',
            field=models.CharField(choices=[('single', 'Single'), ('twin', 'Twin'), ('triplet', 'Triplet'), ('quad', 'Quad')], default='single', help_text='Accepted formats: single, twin, triplet, quad', max_length=10, null=True, verbose_name='Born As'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='breed',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Breed', to='breed.Breed', verbose_name='Breed'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='breed_group',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Breed Group'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='coi',
            field=models.DecimalField(blank=True, decimal_places=4, default=0, max_digits=5, verbose_name='COI'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='current_owner',
            field=models.ForeignKey(blank=True, help_text='Often the same as Breeder', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owner', to='breeder.Breeder', verbose_name='Current Owner'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='custom_fields',
            field=models.TextField(blank=True, verbose_name='Custom Fields'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='date_added',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Date Added'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='date_of_registration',
            field=models.DateField(blank=True, help_text='Date formats: 1984/09/31, 84/09/31, 31/09/1984, 31/09/84, 1984-09-31, 84-09-31, 31-09-1984, 31-09-84', null=True, verbose_name='Date of Registration'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='dob',
            field=models.DateField(blank=True, help_text='Date formats: 1984/09/31, 84/09/31, 31/09/1984, 31/09/84, 1984-09-31, 84-09-31, 31-09-1984, 31-09-84', null=True, verbose_name='Date of Birth'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='dod',
            field=models.DateField(blank=True, help_text='Date formats: 1984/09/31, 84/09/31, 31/09/1984, 31/09/84, 1984-09-31, 84-09-31, 31-09-1984, 31-09-84', null=True, verbose_name='Date of Death'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='mean_kinship',
            field=models.DecimalField(blank=True, decimal_places=4, default=0, max_digits=5, verbose_name='Mean Kinship'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='parent_father',
            field=models.ForeignKey(blank=True, help_text='This should be the parents registration number.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='father', to='pedigree.Pedigree', verbose_name='Father'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='parent_mother',
            field=models.ForeignKey(blank=True, help_text='This should be the parents registration number.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mother', to='pedigree.Pedigree', verbose_name='Mother'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='reg_no',
            field=models.CharField(blank=True, help_text='Must be unique', max_length=100, unique=True, verbose_name='Registration Number'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='sex',
            field=models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('castrated', 'Castrated')], default='female', help_text='Accepted formats: male, female, castrated', max_length=10, null=True, verbose_name='Sex'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='state',
            field=models.CharField(choices=[('edited', 'Edited'), ('unapproved', 'Unapproved'), ('approved', 'Approved')], default='approved', max_length=10, null=True, verbose_name='State'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='status',
            field=models.CharField(choices=[('dead', 'Dead'), ('alive', 'Alive'), ('unknown', 'Unknown')], default='unknown', help_text='Accepted formats: dead, alive, unknown', max_length=10, null=True, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='pedigree',
            name='tag_no',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Tag Number'),
        ),
    ]