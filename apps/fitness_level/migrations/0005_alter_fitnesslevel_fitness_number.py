# Generated by Django 3.2.7 on 2021-10-15 09:25

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fitness_level", "0004_alter_fitnesslevel_fitness_number"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fitnesslevel",
            name="fitness_number",
            field=models.PositiveBigIntegerField(
                unique=True, validators=[django.core.validators.MinValueValidator(1)]
            ),
        ),
    ]