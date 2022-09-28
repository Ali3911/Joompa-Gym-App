# Generated by Django 3.2.7 on 2021-09-30 11:41

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BaselineAssessment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.CharField(max_length=250)),
                ("control_type", models.CharField(max_length=100)),
                ("required", models.BooleanField(default=True)),
                ("options", models.JSONField()),
            ],
        ),
    ]