# Generated by Django 3.2.7 on 2021-11-29 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("v1", "0005_userprogramdesign"),
    ]

    operations = [
        migrations.AddField(
            model_name="userequipment",
            name="weight_type",
            field=models.CharField(choices=[("kg", "kg"), ("lbs", "lbs")], default="kg", max_length=5),
        ),
    ]
