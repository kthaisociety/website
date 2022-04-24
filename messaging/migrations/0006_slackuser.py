# Generated by Django 3.1.13 on 2022-04-24 15:45

import app.storage
from django.conf import settings
from django.db import migrations, models, transaction
import django.db.models.deletion
import uuid
import versatileimagefield.fields


def create_slack_users(apps, schema_editor):
    SlackUser = apps.get_model("messaging", "SlackUser")
    User = apps.get_model("user", "User")

    with transaction.atomic():
        for user in User.objects.filter(slack_id__isnull=False):
            SlackUser.objects.create(
                user=user,
                external_id=user.slack_id,
                token=user.slack_token,
                scopes=user.slack_scopes,
                display_name=user.slack_display_name,
            )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("messaging", "0005_slacklog_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="SlackUser",
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
                ("external_id", models.CharField(max_length=255)),
                ("token", models.CharField(blank=True, max_length=255, null=True)),
                ("scopes", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "display_name",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "picture",
                    versatileimagefield.fields.VersatileImageField(
                        blank=True,
                        null=True,
                        storage=app.storage.OverwriteStorage(),
                        upload_to="messaging/slackuser/picture/",
                        verbose_name="Slack image",
                    ),
                ),
                (
                    "picture_hash",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="slack_user",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.RunPython(create_slack_users, migrations.RunPython.noop),
    ]
