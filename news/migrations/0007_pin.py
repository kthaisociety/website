# Generated by Django 3.1.13 on 2022-04-16 12:55

from django.db import migrations, models
import uuid
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0006_fact_factpost"),
    ]

    operations = [
        migrations.CreateModel(
            name="Pin",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("subtitle", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "picture",
                    versatileimagefield.fields.VersatileImageField(
                        upload_to="news/pin/", verbose_name="Image"
                    ),
                ),
                ("body", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
