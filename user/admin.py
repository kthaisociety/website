from django.contrib import admin, messages

from user.models import User, Team, Division, Role
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
    search_fields = (
        "id",
        "email",
        "name",
        "surname",
        "type",
    )
    list_display = ("email", "name", "surname", "type", "slack_id", "created_at")
    list_filter = (
        "type",
        "email_verified",
        "registration_finished",
        "is_active",
        "gender",
        "university",
        "degree",
        "graduation_year",
    )
    readonly_fields = ("slack_id", "password", "last_login", "created_at")
    ordering = ("-created_at",)
    actions = [send_welcome, send_slack_invite]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(name__isnull=True).exclude(name="")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    search_fields = ("id",)
    list_display = ("id", "starts_at", "ends_at")
    list_filter = ("starts_at", "ends_at")
    ordering = ("-starts_at",)


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    search_fields = ("id", "name")
    list_display = ("id", "name", "team")
    list_filter = ("team",)
    ordering = ("-team__starts_at", "name")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    search_fields = ("id", "user", "division")
    list_display = ("id", "division", "user", "starts_at", "ends_at", "is_head")
    list_filter = ("division__team", "user", "starts_at", "ends_at")
    ordering = ("-division__team__starts_at", "-starts_at", "user")
