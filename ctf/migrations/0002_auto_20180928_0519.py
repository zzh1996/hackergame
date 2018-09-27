# Generated by Django 2.1.1 on 2018-09-27 21:19

from django.db import migrations, models
import django.utils.timezone
import utils.models


class Migration(migrations.Migration):

    dependencies = [
        ('ctf', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimerSwitch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(default=django.utils.timezone.now)),
                ('on_off', models.BooleanField()),
                ('note', models.TextField(blank=True)),
            ],
            bases=(utils.models.UpdateCacheMixin, models.Model),
        ),
        migrations.AlterModelManagers(
            name='problem',
            managers=[
            ],
        ),
    ]