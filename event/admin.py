from django.contrib import admin, messages
from django.db import transaction
from django.forms import ModelForm

import event.api.event.calendar
from event.enums import RegistrationStatus
from event.models import Event, Registration, Session, Attachment, Schedule
from event.tasks import send_url_email
from messaging.api.slack.announcement import announce_event


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "session")
    list_display = ("name", "session", "type", "status")
    list_filter = ("session", "type", "status")
    ordering = ("-created_at", "-updated_at")


class AttachmentInline(admin.StackedInline):
    model = Attachment
    ordering = ("name", "created_at")
    show_change_link = True
    extra = 0


class ScheduleInline(admin.StackedInline):
    model = Schedule
    ordering = ("starts_at",)
    show_change_link = True
    extra = 0


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "event")
    list_display = ("name", "event", "starts_at", "ends_at")
    list_filter = ("starts_at", "ends_at")
    ordering = ("-created_at", "-updated_at", "name")
    readonly_fields = ("google_id",)
    inlines = [AttachmentInline, ScheduleInline]


class SessionInline(admin.StackedInline):
    model = Session
    ordering = ("starts_at", "ends_at", "name")
    exclude = ("google_id",)
    show_change_link = True
    extra = 0


def send_url(modeladmin, request, registrations):
    for registration in registrations:
        send_url_email(registration_id=registration.id)
    messages.success(
        request,
        f"Link emails have been sent to {registrations.count()} registration/s.",
    )


send_url.short_description = "Send link email"


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    search_fields = ("id", "event", "user")
    list_display = ("id", "event", "user", "status")
    list_filter = ("event", "status")
    ordering = ("-created_at", "-updated_at")
    actions = [send_url]


class RegistrationInline(admin.StackedInline):
    model = Registration
    ordering = ("-created_at",)
    show_change_link = False
    can_delete = False
    extra = 0
    readonly_fields = ("user", "status", "created_at")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


def send_slack_announcement(modeladmin, request, events):
    for event in events:
        announce_event(event=event, creator_id=request.user.id)
    messages.success(
        request, f"Slack announcements have been posted for {events.count()} event/s."
    )


send_slack_announcement.short_description = "Send Slack announcement"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "code", "type", "status")
    list_display = ("name", "code", "type", "status", "registration_count")
    list_filter = ("type", "status")
    ordering = ("-created_at", "-updated_at", "name")
    inlines = [SessionInline, RegistrationInline]
    actions = [send_slack_announcement]

    def registration_count(self, obj):
        return obj.registrations.filter(
            status__in=[
                RegistrationStatus.REGISTERED,
                RegistrationStatus.JOINED,
                RegistrationStatus.ATTENDED,
            ]
        ).count()

    registration_count.short_description = "registrations"
