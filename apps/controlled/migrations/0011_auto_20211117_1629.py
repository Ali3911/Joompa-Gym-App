# Generated by Django 3.2.7 on 2021-11-17 16:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("injury", "0008_rename_status_injury_required"),
        ("controlled", "0010_auto_20211110_0745"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="controlprogram",
            name="joint_injury",
        ),
        migrations.RemoveField(
            model_name="controlprogram",
            name="muscle_injury",
        ),
        migrations.CreateModel(
            name="ControlProgramInjury",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "control_program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cp_injuries",
                        to="controlled.controlprogram",
                    ),
                ),
                (
                    "injury",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="cpi_injury", to="injury.injury"
                    ),
                ),
                (
                    "injury_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cpi_injury_type",
                        to="injury.injurytype",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]