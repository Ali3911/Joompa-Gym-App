# Generated by Django 3.2.7 on 2021-10-06 15:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("fitness_level", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="fitnesslevel",
            options={"ordering": ["-created_at"]},
        ),
    ]
