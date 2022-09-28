# Generated by Django 3.2.7 on 2021-11-02 12:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("body_part", "0002_alter_bodypart_name"),
        ("injury", "0006_alter_injury_injury_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="injury",
            name="body_part",
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to="body_part.bodypart"),
            preserve_default=False,
        ),
    ]