# Generated by Django 4.2 on 2023-05-30 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0054_alter_part_units'),
    ]

    operations = [
        migrations.AlterField(
            model_name='part',
            name='units',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Единицы'),
        ),
    ]
