from django.contrib import admin

from event.models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "code", "type", "status")
    list_display = ("name", "code", "type", "status")
    list_filter = ("type", "status")
    ordering = ("-created_at", "-updated_at", "name")
