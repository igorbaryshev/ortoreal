# Generated by Django 4.1.7 on 2023-04-03 18:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_is_prosthetist_user_surname_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'Работник', 'verbose_name_plural': 'Работники'},
        ),
    ]
