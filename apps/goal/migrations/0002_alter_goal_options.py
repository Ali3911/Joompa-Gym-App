# Generated by Django 3.2.7 on 2021-10-06 15:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("goal", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="goal",
            options={"ordering": ["-created_at"]},
        ),
    ]