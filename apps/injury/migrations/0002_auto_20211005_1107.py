# Generated by Django 3.2.7 on 2021-10-05 11:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("injury", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="InjuryType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=250)),
            ],
        ),
        migrations.AlterModelOptions(
            name="injury",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddField(
            model_name="injury",
            name="status",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="injury",
            name="injury_type",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="injury.injurytype"),
        ),
    ]
