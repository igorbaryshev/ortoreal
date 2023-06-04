# Generated by Django 4.2 on 2023-05-29 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0053_alter_part_note'),
    ]

    operations = [
        migrations.AlterField(
            model_name='part',
            name='units',
            field=models.CharField(blank=True, choices=[('pairs', 'пар'), ('pieces', 'шт.'), ('sets', 'компл.'), ('packages', 'упак.'), ('items', 'ед.'), ('meters', 'м.')], default='items', max_length=32, null=True, verbose_name='Единицы'),
        ),
    ]