# Generated by Django 4.1.7 on 2023-04-14 14:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_client_ipr_client_snils_client_sprmse_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='client',
            old_name='bank_detail',
            new_name='bank_details',
        ),
    ]
