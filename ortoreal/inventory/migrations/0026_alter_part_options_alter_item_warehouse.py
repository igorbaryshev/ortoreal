# Generated by Django 4.1.7 on 2023-04-24 02:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0025_item_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='part',
            options={'verbose_name': 'модель комплектующего', 'verbose_name_plural': 'Номенклатура'},
        ),
        migrations.AlterField(
            model_name='item',
            name='warehouse',
            field=models.CharField(blank=True, choices=[('s1', 'Склад 1'), ('s2', 'Склад 2')], default='', max_length=16, verbose_name='Склад'),
            preserve_default=False,
        ),
    ]
