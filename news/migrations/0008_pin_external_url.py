# Generated by Django 3.1.13 on 2022-04-24 09:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0007_pin"),
    ]

    operations = [
        migrations.AddField(
            model_name="pin",
            name="external_url",
            field=models.URLField(blank=True, null=True),
        ),
    ]
