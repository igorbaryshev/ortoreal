# Generated by Django 4.2 on 2023-08-09 07:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0042_alter_bankdetails_account_number_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bankdetails',
            options={'verbose_name': 'реквизиты'},
        ),
        migrations.RemoveField(
            model_name='client',
            name='bank_details',
        ),
    ]
