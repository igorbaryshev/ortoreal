# Generated by Django 4.2 on 2023-07-10 01:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0028_alter_contacttypechoice_worker'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contacttypechoice',
            name='worker',
        ),
        migrations.AddField(
            model_name='contacttypechoice',
            name='prosthetist',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_prosthetist': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='протезист'),
        ),
    ]