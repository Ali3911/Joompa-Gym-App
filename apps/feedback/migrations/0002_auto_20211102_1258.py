# Generated by Django 3.2.7 on 2021-11-02 12:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("feedback", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="feedbackrange",
            name="feedback",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="fr_feedbacks", to="feedback.feedback"
            ),
        ),
        migrations.AlterField(
            model_name="feedbackvalue",
            name="feedback",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="fv_feedbacks", to="feedback.feedback"
            ),
        ),
    ]
