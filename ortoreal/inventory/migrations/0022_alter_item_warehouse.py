# Generated by Django 4.1.7 on 2023-04-17 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0021_prosthesismodel_item_client_item_prosthetist_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='warehouse',
            field=models.CharField(choices=[('s1', 'Склад 1'), ('s2', 'Склад 2')], max_length=16, null=True, verbose_name='Склад'),
        ),
    ]
