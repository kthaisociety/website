# Generated by Django 3.1.13 on 2022-04-24 16:01

import app.storage
from django.db import migrations
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0006_slackuser"),
    ]

    operations = [
        migrations.AddField(
            model_name="slackuser",
            name="picture_original",
            field=versatileimagefield.fields.VersatileImageField(
                blank=True,
                null=True,
                storage=app.storage.OverwriteStorage(),
                upload_to="messaging/slackuser/picture/original/",
                verbose_name="Slack original image",
            ),
        ),
    ]
