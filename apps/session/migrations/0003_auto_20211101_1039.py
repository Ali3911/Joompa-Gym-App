# Generated by Django 3.2.7 on 2021-11-01 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0002_remove_session_length'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='session',
            name='session',
        ),
        migrations.AddField(
            model_name='session',
            name='description',
            field=models.CharField(default='session', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='session',
            name='value',
            field=models.PositiveIntegerField(default=1, unique=True),
            preserve_default=False,
        ),
    ]
