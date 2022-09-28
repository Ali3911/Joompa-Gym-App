# Generated by Django 3.2.7 on 2021-10-25 10:13

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("goal", "0004_goal_required"),
        ("reps_in_reserve", "0004_remove_repsinreserve_value"),
    ]

    operations = [
        migrations.CreateModel(
            name="RepsRange",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("value", models.PositiveIntegerField()),
                ("range_name", models.CharField(max_length=2)),
                (
                    "goal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="goals", to="goal.goal"
                    ),
                ),
            ],
            options={
                "unique_together": {("goal", "value", "range_name")},
            },
        ),
        migrations.CreateModel(
            name="RepsRating",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("weight", models.IntegerField()),
                ("reps", models.IntegerField()),
                (
                    "rating",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MaxValueValidator(3),
                            django.core.validators.MinValueValidator(-3),
                        ]
                    ),
                ),
                (
                    "reps_range",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reps_ranges",
                        to="reps_in_reserve.repsrange",
                    ),
                ),
            ],
            options={
                "unique_together": {("rating", "reps_range")},
            },
        ),
    ]
