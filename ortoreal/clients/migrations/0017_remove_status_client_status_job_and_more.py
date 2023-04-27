# Generated by Django 4.1.7 on 2023-04-26 06:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0016_alter_client_region_alter_contact_client'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='status',
            name='client',
        ),
        migrations.AddField(
            model_name='status',
            name='job',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='statuses', to='clients.job', verbose_name='Работа'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='job',
            name='prosthetist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='jobs', to=settings.AUTH_USER_MODEL, verbose_name='Протезист'),
        ),
    ]
