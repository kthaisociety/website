from django.contrib import admin, messages
from django.http import HttpResponse
import csv
from django.contrib.auth.models import Group

from app.settings import GROUP_BY_DIVISION_NAME
from user.models import Division, History, Role, Team, User
from user.utils import send_imported, send_slack


def send_welcome(modeladmin, request, users):
    for user in users:
        send_imported(user=user)
    messages.success(
        request, f"Welcome emails have been sent to {users.count()} user/s."
    )


def send_slack_invite(modeladmin, request, users):
    for user in users:
        send_slack(user=user)
    messages.success(
        request, f"Slack invitations have been sent to {users.count()} user/s."
    )


send_welcome.short_description = "Send welcome email"
send_slack_invite.short_description = "Send Slack invitation"


def export_users_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=users.csv"

    writer = csv.writer(response)
    # Header row (keep it concise; add more fields if needed)
    writer.writerow(
        [
            "id",
            "email",
            "name",
            "surname",
            "is_active",
            "is_admin",
            "created_at",
        ]
    )
    for u in queryset.select_related("slack_user").all():
        writer.writerow(
            [
                u.id,
                u.email,
                u.name,
                u.surname,
                u.is_active,
                u.is_admin,
                u.created_at.isoformat(),
            ]
        )

    return response

export_users_csv.short_description = "Export selected users (CSV)"

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ("id", "email", "name", "surname", "type")
    list_display = (
        "email",
        "name",
        "surname",
        "type",
        "email_verified",
        "registration_finished",
        "is_active",
        "slack_user",
        "created_at",
    )
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
    readonly_fields = (
        "groups",
        "last_login",
        "slack_user",
        "created_at",
    )
    exclude = ("password", "user_permissions")
    ordering = ("-created_at",)
    actions = [send_welcome, send_slack_invite, export_users_csv]


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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        group_names = GROUP_BY_DIVISION_NAME.get(obj.division.name, [])
        for group in Group.objects.filter(name__in=group_names):
            if obj.is_active:
                obj.user.groups.add(group)
            else:
                obj.user.groups.remove(group)


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    search_fields = ("id", "title", "body")
    list_display = ("title", "time")
    list_filter = ("time",)
    ordering = ("-time",)
