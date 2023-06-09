# Generated by Django 4.1.7 on 2023-04-10 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0017_alter_part_units'),
    ]

    operations = [
        migrations.AlterField(
            model_name='part',
            name='units',
            field=models.CharField(blank=True, choices=[('pairs', 'пар'), ('pieces', 'шт.'), ('sets', 'компл.'), ('packages', 'упак.'), ('items', 'ед.')], default='items', max_length=32, verbose_name='Единицы'),
        ),
    ]
