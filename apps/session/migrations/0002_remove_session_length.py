# Generated by Django 3.2.7 on 2021-10-07 07:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("session", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="session",
            name="length",
        ),
    ]
