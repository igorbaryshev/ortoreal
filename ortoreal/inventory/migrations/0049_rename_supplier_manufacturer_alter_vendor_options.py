# Generated by Django 4.2 on 2023-05-26 14:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0048_supplier_alter_vendor_options'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Supplier',
            new_name='Manufacturer',
        ),
        migrations.AlterModelOptions(
            name='vendor',
            options={'verbose_name': 'Поставщик', 'verbose_name_plural': 'Поставщики'},
        ),
    ]
