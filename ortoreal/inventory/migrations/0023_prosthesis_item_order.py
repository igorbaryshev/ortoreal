# Generated by Django 4.1.7 on 2023-04-18 23:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0012_alter_status_options_alter_status_name_order'),
        ('inventory', '0022_alter_item_warehouse'),
    ]

    operations = [
        migrations.CreateModel(
            name='Prosthesis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=150, unique=True, verbose_name='Номер изделия')),
                ('kind', models.CharField(blank=True, max_length=1024, verbose_name='Вид')),
                ('name', models.CharField(blank=True, max_length=1024, verbose_name='Наименование')),
                ('price', models.DecimalField(decimal_places=2, max_digits=11, verbose_name='Стоимость')),
            ],
            options={
                'verbose_name': 'Протез',
                'verbose_name_plural': 'Протезы',
            },
        ),
        migrations.AddField(
            model_name='item',
            name='order',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='clients.order', verbose_name='Заказ'),
        ),
    ]
