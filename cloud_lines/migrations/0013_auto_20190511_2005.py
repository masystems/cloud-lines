# Generated by Django 2.1.7 on 2019-05-11 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud_lines', '0012_faq'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='image',
            field=models.ImageField(blank=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='page',
            name='sub_title',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
