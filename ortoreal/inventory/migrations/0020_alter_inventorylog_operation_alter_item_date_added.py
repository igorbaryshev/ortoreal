# Generated by Django 4.1.7 on 2023-04-14 13:34

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0019_inventorylog_client'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorylog',
            name='operation',
            field=models.CharField(choices=[('', '---выбрать---'), ('RECEIVED', 'Приход'), ('RETURNED', 'Вернул'), ('TOOK', 'Взял')], max_length=32, verbose_name='Операция'),
        ),
        migrations.AlterField(
            model_name='item',
            name='date_added',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Дата'),
        ),
    ]
