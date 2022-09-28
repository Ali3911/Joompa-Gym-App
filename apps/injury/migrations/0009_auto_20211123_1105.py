# Generated by Django 3.2.7 on 2021-11-23 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("body_part", "0002_alter_bodypart_name"),
        ("injury", "0008_rename_status_injury_required"),
    ]

    operations = [
        migrations.AlterField(
            model_name="injury",
            name="name",
            field=models.CharField(max_length=250),
        ),
        migrations.AlterUniqueTogether(
            name="injury",
            unique_together={("name", "body_part", "injury_type")},
        ),
    ]