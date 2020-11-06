from django.contrib import admin, messages

from event.models import Event, Registration, Session, Attachment, Schedule
from event.tasks import send_url_email


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
    inlines = [AttachmentInline, ScheduleInline]


class SessionInline(admin.StackedInline):
    model = Session
    ordering = ("starts_at", "ends_at", "name")
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

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "code", "type", "status")
    list_display = ("name", "code", "type", "status")
    list_filter = ("type", "status")
    ordering = ("-created_at", "-updated_at", "name")
    inlines = [SessionInline, RegistrationInline]
