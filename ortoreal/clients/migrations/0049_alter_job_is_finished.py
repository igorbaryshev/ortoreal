# Generated by Django 4.2.4 on 2023-08-24 05:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0048_job_is_finished'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='is_finished',
            field=models.BooleanField(default=False, verbose_name='завершена'),
        ),
    ]
