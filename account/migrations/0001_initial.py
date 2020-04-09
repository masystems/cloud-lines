# Generated by Django 2.1.9 on 2019-06-21 07:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cloud_lines', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AttachedService',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('animal_type', models.CharField(max_length=250)),
                ('site_mode', models.CharField(blank=True, choices=[('mammal', 'Mammal'), ('poultry', 'Poultry')], default=None, max_length=13, null=True)),
                ('increment', models.CharField(blank=True, choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')], default=None, max_length=10, null=True)),
                ('active', models.BooleanField(default=False)),
                ('install_available', models.BooleanField(default=False)),
                ('admin_users', models.ManyToManyField(blank=True, related_name='admin_users', to=settings.AUTH_USER_MODEL)),
                ('read_only_users', models.ManyToManyField(blank=True, related_name='read_only_users', to=settings.AUTH_USER_MODEL)),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='cloud_lines.Service')),
            ],
        ),
        migrations.CreateModel(
            name='UserDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(max_length=15)),
                ('stripe_id', models.CharField(blank=True, max_length=50)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='attachedservice',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attached_service', to='account.UserDetail'),
        ),
    ]
