# Generated by Django 3.2.7 on 2021-10-13 09:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("reps_in_reserve", "0003_alter_repsinreserve_weeks"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="repsinreserve",
            name="value",
        ),
    ]
