from django.contrib import admin

from event.models import Event, Registration, Session


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


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    search_fields = ("id", "event", "user")
    list_display = ("id", "event", "user", "status")
    list_filter = ("event", "status")
    ordering = ("-created_at", "-updated_at")
