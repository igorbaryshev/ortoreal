# Generated by Django 4.1.7 on 2023-04-21 18:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0024_order_remove_item_client_remove_item_order_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='order',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='inventory.order', verbose_name='Заказ'),
        ),
    ]
