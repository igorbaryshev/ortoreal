# Generated by Django 4.1.7 on 2023-04-21 18:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0015_contact_client_alter_contact_result'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='region',
            field=models.CharField(blank=True, choices=[('Moscow', 'Москва'), ('Moscow region', 'Московская область')], default=None, max_length=128, verbose_name='Регион'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clients.client', verbose_name='Клиент'),
        ),
    ]
