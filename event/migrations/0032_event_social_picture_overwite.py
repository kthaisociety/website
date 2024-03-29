# Generated by Django 3.1.13 on 2022-11-14 14:07

import app.storage
from django.db import migrations
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ("event", "0031_event_signup_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="social_picture",
            field=versatileimagefield.fields.VersatileImageField(
                blank=True,
                null=True,
                storage=app.storage.OverwriteStorage(),
                upload_to="event/social/",
                verbose_name="Social image",
            ),
        ),
    ]
