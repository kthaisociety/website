from django.contrib import admin, messages

from event.models import Event, Registration, Session
from event.tasks import send_url_email


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "code", "type", "status")
    list_display = ("name", "code", "type", "status")
    list_filter = ("type", "status")
    ordering = ("-created_at", "-updated_at", "name")


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "event")
    list_display = ("name", "event", "starts_at", "ends_at")
    list_filter = ("starts_at", "ends_at")
    ordering = ("-created_at", "-updated_at", "name")


def send_url(modeladmin, request, registrations):
    for registration in registrations:
        send_url_email(registration_id=registration.id)
    messages.success(
        request, f"Link emails have been sent to {registrations.count()} registration/s."
    )


send_url.short_description = "Send link email"


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    search_fields = ("id", "event", "user")
    list_display = ("id", "event", "user", "status")
    list_filter = ("event", "status")
    ordering = ("-created_at", "-updated_at")
    actions = [send_url]
