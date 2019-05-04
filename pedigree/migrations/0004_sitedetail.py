# Generated by Django 2.1.7 on 2019-02-26 20:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedigree', '0003_auto_20190221_2051'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('animal', models.CharField(max_length=250)),
                ('site_mode', models.CharField(choices=[('hierarchy', 'Hierarchy'), ('breed_groups', 'Breed Groups')], default=None, max_length=13)),
                ('install_available', models.BooleanField(default=False)),
            ],
        ),
    ]
