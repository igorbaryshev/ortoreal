# Generated by Django 4.2 on 2023-08-09 07:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0038_remove_client_passport_client_birth_date_passport'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contact',
            options={'verbose_name': 'обращение', 'verbose_name_plural': 'обращения'},
        ),
        migrations.AlterModelOptions(
            name='passport',
            options={'verbose_name': 'паспортные данные'},
        ),
    ]
