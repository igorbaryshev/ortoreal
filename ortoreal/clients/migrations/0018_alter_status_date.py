# Generated by Django 4.1.7 on 2023-04-26 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0017_remove_status_client_status_job_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='status',
            name='date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата'),
        ),
    ]
