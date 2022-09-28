# Generated by Django 3.2.7 on 2021-11-17 11:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("goal", "0005_goal_gender"),
        ("fitness_level", "0005_alter_fitnesslevel_fitness_number"),
        ("reps_in_reserve", "0006_alter_repsrange_value"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="repsinreserve",
            unique_together={("fitness_level", "goal")},
        ),
    ]