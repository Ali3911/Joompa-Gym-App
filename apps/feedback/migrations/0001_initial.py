# Generated by Django 3.2.7 on 2021-11-02 11:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Feedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=250, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="FeedbackValue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.CharField(max_length=250)),
                ("value", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("feedback", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="feedback.feedback")),
            ],
        ),
        migrations.CreateModel(
            name="FeedbackRange",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=250)),
                ("rir", models.CharField(max_length=250)),
                ("range_lower_limit", models.PositiveIntegerField()),
                ("range_upper_limit", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("feedback", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="feedback.feedback")),
            ],
        ),
    ]
