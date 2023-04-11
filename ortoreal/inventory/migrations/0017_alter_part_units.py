# Generated by Django 4.1.7 on 2023-04-10 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0016_remove_inventorylog_patient_delete_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='part',
            name='units',
            field=models.CharField(blank=True, choices=[('пар', 'Pairs'), ('шт.', 'Pieces'), ('компл.', 'Sets'), ('упак.', 'Packages')], max_length=32, verbose_name='Единицы'),
        ),
    ]