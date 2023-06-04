# Generated by Django 4.2 on 2023-05-31 19:07

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0059_alter_inventorylog_options_alter_item_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='price',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=11, verbose_name='цена, руб.'),
        ),
    ]
