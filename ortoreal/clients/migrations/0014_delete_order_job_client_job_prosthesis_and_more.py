# Generated by Django 4.1.7 on 2023-04-21 05:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0024_order_remove_item_client_remove_item_order_and_more'),
        ('clients', '0013_job_remove_order_client_remove_order_prosthetist_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.DeleteModel(
            name='Order',
        ),
        migrations.AddField(
            model_name='job',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clients.client', verbose_name='Клиент'),
        ),
        migrations.AddField(
            model_name='job',
            name='prosthesis',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.prosthesis', verbose_name='Протез'),
        ),
        migrations.AddField(
            model_name='job',
            name='prosthetist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Протезист'),
        ),
    ]
