# Generated by Django 3.2.7 on 2021-12-22 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("v1", "0011_auto_20211213_1233"),
    ]

    operations = [
        migrations.AddField(
            model_name="userstandardvariable",
            name="unit",
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
