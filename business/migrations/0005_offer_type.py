# Generated by Django 3.1.13 on 2022-10-29 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("business", "0004_company_ordering"),
    ]

    operations = [
        migrations.AlterField(
            model_name="offer",
            name="type",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, "INTERNSHIP"),
                    (1, "SUMMER_INTERNSHIP"),
                    (2, "PART_TIME"),
                    (3, "FULL_TIME"),
                    (4, "VOLUNTEER"),
                    (5, "OTHER"),
                    (6, "MASTER_THESIS"),
                ],
                default=0,
            ),
        ),
    ]
