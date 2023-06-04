# Generated by Django 4.2 on 2023-05-29 19:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0051_item_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='part',
            name='vendor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='inventory.vendor', verbose_name='Поставщик'),
        ),
    ]