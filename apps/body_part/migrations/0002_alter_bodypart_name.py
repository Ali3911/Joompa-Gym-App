# Generated by Django 3.2.7 on 2021-10-20 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("body_part", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bodypart",
            name="name",
            field=models.CharField(max_length=100),
        ),
    ]
