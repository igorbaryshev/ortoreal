# Generated by Django 4.2 on 2023-05-10 17:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0020_alter_client_prosthetist_alter_job_prosthetist'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to='clients.client', verbose_name='Клиент'),
        ),
    ]
