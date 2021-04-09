# Generated by Django 2.2.18 on 2021-03-28 16:40

from django.db import migrations
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [("event", "0019_schedule_type_enums")]

    operations = [
        migrations.AddField(
            model_name="event",
            name="social_picture",
            field=versatileimagefield.fields.VersatileImageField(
                blank=True,
                null=True,
                upload_to="event/social/",
                verbose_name="Social image",
            ),
        )
    ]