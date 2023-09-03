# Generated by Django 4.2.4 on 2023-08-24 07:45

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0052_remove_status_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='status',
            name='color',
            field=colorfield.fields.ColorField(choices=[('in work', 'B6D7A8'), ('issued', '6AA84F'), ('docs submitted', '34A853'), ('payment to client', '00FFFF'), ('payment', '6D9EEB')], default='in work', image_field=None, max_length=18, samples=None),
        ),
    ]