# Generated by Django 3.2.7 on 2021-10-13 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reps_in_reserve", "0002_auto_20211004_1444"),
    ]

    operations = [
        migrations.AlterField(
            model_name="repsinreserve",
            name="weeks",
            field=models.JSONField(max_length=250),
        ),
    ]