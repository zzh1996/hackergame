# Generated by Django 2.1.12 on 2019-10-05 05:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submission', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='score',
            unique_together={('user', 'category')},
        ),
    ]
