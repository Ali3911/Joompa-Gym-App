# Generated by Django 3.2.7 on 2021-10-11 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("goal", "0002_alter_goal_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="goal",
            name="name",
            field=models.CharField(max_length=250, unique=True),
        ),
    ]
