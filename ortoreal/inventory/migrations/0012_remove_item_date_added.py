# Generated by Django 4.1.7 on 2023-04-06 00:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_alter_inventorylog_date_alter_item_date_added_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='date_added',
        ),
    ]