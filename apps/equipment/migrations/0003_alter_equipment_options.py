# Generated by Django 3.2.7 on 2021-10-06 15:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0002_alter_equipment_image"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="equipment",
            options={"ordering": ["-created_at"]},
        ),
    ]
