# Generated by Django 3.2.7 on 2021-11-26 10:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0008_equipment_type"),
        ("v1", "0002_auto_20211123_1014"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userprofile",
            name="equipment_option",
        ),
        migrations.AddField(
            model_name="userequipment",
            name="equipment_option",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user_equipment_options",
                to="equipment.equipmentoption",
            ),
        ),
    ]
