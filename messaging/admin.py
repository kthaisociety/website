from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils.safestring import mark_safe

from app.utils import ReadOnlyAdmin
from messaging.models import SlackChannel, SlackLog

import messaging.api.slack.channel


def invite_users(modeladmin, request, channels):
    success_channels = []
    error_channels = []
    for channel in channels:
        if messaging.api.slack.channel.invite_users(external_id=channel.external_id):
            success_channels.append(channel)
        else:
            error_channels.append(channel)
    if success_channels:
        messages.success(
            request,
            f"All Slack valid users have been invited to {', '.join([str(channel) for channel in success_channels])}.",
        )
    if error_channels:
        messages.error(
            request,
            f"Slack valid users could not be invited to {', '.join([str(channel) for channel in error_channels])}.",
        )


@admin.register(SlackChannel)
class SlackChannelAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "external_id")
    list_display = (
        "name",
        "external_id",
        "is_general",
        "topic",
        "purpose",
        "num_members",
    )
    list_filter = ("is_general", "is_archived", "is_private")
    exclude = ("external_creator_id",)
    ordering = ("name",)
    actions = [invite_users]

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [
            "external_id",
            "external_created_at",
            "is_general",
            "is_archived",
            "is_private",
            "num_members",
            "created_at",
            "updated_at",
            "creator",
        ]
        if obj and obj.is_general:
            readonly_fields += ["name"]
        return readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:
            transaction.on_commit(
                lambda: messaging.api.slack.channel.create(
                    name=obj.name, topic=obj.topic, purpose=obj.purpose
                )
            )
        else:
            if "name" in form.changed_data:
                if messaging.api.slack.channel.set_name(
                    external_id=obj.external_id, name=obj.name
                ):
                    messages.success(
                        request, f"Slack channel name has been sent to {obj.name}."
                    )
                else:
                    messages.error(
                        request, f"Failed to set Slack channel name to {obj.name}."
                    )
            if "topic" in form.changed_data:
                if messaging.api.slack.channel.set_topic(
                    external_id=obj.external_id, topic=obj.topic
                ):
                    messages.success(
                        request, f"Slack channel topic has been sent to {obj.topic}."
                    )
                else:
                    messages.error(
                        request, f"Failed to set Slack channel topic to {obj.topic}."
                    )
            if "purpose" in form.changed_data:
                if messaging.api.slack.channel.set_purpose(
                    external_id=obj.external_id, purpose=obj.purpose
                ):
                    messages.success(
                        request,
                        f"Slack channel purpose has been sent to {obj.purpose}.",
                    )
                else:
                    messages.error(
                        request,
                        f"Failed to set Slack channel purpose to {obj.purpose}.",
                    )
        super().save_model(request, obj, form, change)

    def creator(self, obj):
        if obj.creator:
            return mark_safe(
                f"<a href='{reverse('admin:user_user_change', args=(str(obj.creator.id),))}'>{obj.creator}</a>"
            )
        return "-"

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SlackLog)
class SlackLogAdmin(ReadOnlyAdmin):
    search_fields = ("id", "type", "channel")
    list_display = ("id", "type", "channel", "user")
    list_filter = ("type", "channel", "user")
    ordering = ("-created_at",)
