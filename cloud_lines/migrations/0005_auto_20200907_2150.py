# Generated by Django 2.2.11 on 2020-09-07 21:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud_lines', '0004_auto_20200422_1743'),
    ]

    operations = [
        migrations.AlterField(
            model_name='update',
            name='body',
            field=models.TextField(default='<strong>Features</strong>\n    <br>\n        <ul class="list-icons">\n            <li><i class="fad fa-check text-info"></i> </li>\n        </ul>\n<strong>Bug Fixes</strong>\n        <ul class="list-icons">\n            <li><i class="fad fa-check text-info"></i> </li>\n        </ul>'),
        ),
    ]
