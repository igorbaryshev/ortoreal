# Generated by Django 4.2.7 on 2023-12-01 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0056_alter_status_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='address',
            field=models.TextField(max_length=1000, verbose_name='адрес'),
        ),
    ]
