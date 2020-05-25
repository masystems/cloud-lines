# Generated by Django 2.2.11 on 2020-04-16 14:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Faq',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=250)),
                ('answer', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=100)),
                ('image', models.ImageField(blank=True, upload_to='')),
                ('detail', models.CharField(blank=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50, unique=True)),
                ('sub_title', models.CharField(blank=True, max_length=150)),
                ('body', models.TextField()),
                ('image', models.ImageField(blank=True, upload_to='')),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ordering', models.IntegerField()),
                ('active', models.BooleanField(default=True)),
                ('icon', models.CharField(blank=True, max_length=500)),
                ('image', models.FileField(blank=True, upload_to='')),
                ('service_name', models.CharField(max_length=50, unique=True)),
                ('admin_users', models.IntegerField()),
                ('contrib_users', models.IntegerField()),
                ('read_only_users', models.IntegerField()),
                ('number_of_animals', models.IntegerField()),
                ('multi_breed', models.BooleanField()),
                ('support', models.BooleanField()),
                ('support_cost_per_year', models.DecimalField(decimal_places=2, max_digits=5)),
                ('price_per_month', models.DecimalField(decimal_places=2, max_digits=5)),
                ('price_per_year', models.DecimalField(decimal_places=2, max_digits=5)),
                ('total_price_per_year', models.DecimalField(decimal_places=2, max_digits=6)),
                ('service_description', models.TextField()),
                ('service_id', models.CharField(blank=True, max_length=100)),
                ('monthly_id', models.CharField(blank=True, max_length=100)),
                ('yearly_id', models.CharField(blank=True, max_length=100)),
                ('service_test_id', models.CharField(blank=True, max_length=100)),
                ('monthly_test_id', models.CharField(blank=True, max_length=100)),
                ('yearly_test_id', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'ordering': ['ordering'],
            },
        ),
        migrations.CreateModel(
            name='Update',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('body', models.TextField(default='<strong>Features</strong>\n    <br>\n        <ul class="list-icons">\n            <li><i class="fa fa-check text-info"></i> </li>\n        </ul>\n<strong>Bug Fixes</strong>\n        <ul class="list-icons">\n            <li><i class="fa fa-check text-info"></i> </li>\n        </ul>')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='Testimonial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('body', models.TextField()),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='cloud_lines.Service')),
            ],
        ),
        migrations.CreateModel(
            name='LargeTierQueue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subdomain', models.CharField(blank=True, max_length=255, unique=True)),
                ('build_state', models.CharField(choices=[('waiting', 'Waiting'), ('building', 'Building'), ('complete', 'Complete')], default='waiting', max_length=20)),
                ('build_status', models.CharField(blank=True, max_length=255)),
                ('percentage_complete', models.IntegerField(default=0, null=True)),
                ('attached_service', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lattached_service', to='account.AttachedService')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='luser', to=settings.AUTH_USER_MODEL)),
                ('user_detail', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_detail', to='account.UserDetail')),
            ],
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('email', models.CharField(max_length=250)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('subject', models.CharField(max_length=250)),
                ('message', models.TextField()),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='cloud_lines.Service')),
            ],
        ),
    ]