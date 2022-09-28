# Generated by Django 3.2.7 on 2021-09-30 11:50

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ("baseline_assessment", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="baselineassessment",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=datetime.datetime(2021, 9, 30, 11, 50, 2, 480394, tzinfo=utc)
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="baselineassessment",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]