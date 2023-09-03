# Generated by Django 4.2.4 on 2023-08-21 04:25

import clients.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0046_remove_contact_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='snils_scan',
            field=models.FileField(blank=True, null=True, upload_to=clients.models.Client.client_directory_path, verbose_name='скан СНИЛС'),
        ),
    ]
