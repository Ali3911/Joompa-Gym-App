# Generated by Django 3.2.7 on 2021-10-18 10:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BodyPart",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("required", models.BooleanField(default=True)),
                (
                    "classification",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="classifications",
                        to="body_part.bodypart",
                    ),
                ),
            ],
            options={
                "verbose_name": "Body Part",
                "verbose_name_plural": "Body Parts",
                "ordering": ["-created_at"],
            },
        ),
    ]
