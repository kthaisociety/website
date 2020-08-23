from django.contrib import admin, messages

from user.models import User
from user.utils import send_imported, slack_invite


def send_welcome(modeladmin, request, users):
    for user in users:
        send_imported(user=user)
    messages.success(
        request, f"Welcome emails have been sent to {users.count()} user/s."
    )


def send_slack_invite(modeladmin, request, users):
    for user in users:
        slack_invite(user=user)
    messages.success(
        request, f"Slack inivtations have been sent to {users.count()} user/s."
    )


send_welcome.short_description = "Send welcome email"
send_slack_invite.short_description = "Send Slack invitation"


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ("id", "email", "name", "surname", "type")
    list_display = ("email", "name", "surname", "type")
    list_filter = ("type", "email_verified", "is_active")
    ordering = ("name", "surname", "email", "type")
    actions = [send_welcome, send_slack_invite]
