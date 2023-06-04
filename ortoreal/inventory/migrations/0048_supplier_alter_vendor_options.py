# Generated by Django 4.2 on 2023-05-26 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0047_alter_part_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1024, unique=True)),
            ],
            options={
                'verbose_name': 'Поставщик',
                'verbose_name_plural': 'Поставщики',
            },
        ),
        migrations.AlterModelOptions(
            name='vendor',
            options={'verbose_name': 'Производитель', 'verbose_name_plural': 'Производители'},
        ),
    ]
