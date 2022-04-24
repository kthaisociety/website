from django import forms
from django.conf.urls import url
from django.contrib import admin, messages
from django.db.models import F
from django.forms import BaseInlineFormSet
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html

from event.api.event.event import get_event_resumes_zip
from event.enums import RegistrationStatus
from event.models import (Attachment, Event, Registration, Schedule, Session,
                          Speaker, SpeakerRole)
from event.tasks import send_url_email
from messaging.api.slack.announcement import announce_event
from user.enums import DietType, UserType


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


class SpeakerRoleInline(admin.StackedInline):
    model = SpeakerRole
    ordering = ("speaker__name",)
    show_change_link = True
    extra = 0


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "event")
    list_display = ("name", "event", "starts_at", "ends_at")
    list_filter = ("starts_at", "ends_at")
    ordering = ("-created_at", "-updated_at", "name")
    readonly_fields = ("google_id",)
    inlines = [SpeakerRoleInline, AttachmentInline, ScheduleInline]


class SessionInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        if not any([cd and not cd.get("DELETE", False) for cd in self.cleaned_data]):
            raise forms.ValidationError("An event must have at least one session.")


class SessionInline(admin.StackedInline):
    model = Session
    ordering = ("starts_at", "ends_at", "name")
    exclude = ("google_id",)
    show_change_link = True
    extra = 0
    formset = SessionInlineFormSet


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
    readonly_fields = ("dietary_restrictions", "user", "status", "created_at")
    exclude = ("diet", "diet_other")

    def dietary_restrictions(self, obj):
        if obj.dietary_restrictions:
            return format_html(
                "<br>".join([DietType.labels[dt] for dt in obj.dietary_restrictions])
            )
        return "-"

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
    list_display = (
        "name",
        "code",
        "type",
        "status",
        "new_user_count",
        "registration_count",
    )
    list_filter = ("type", "status")
    ordering = ("-created_at", "-updated_at", "name")
    readonly_fields = ("diet_restrictions", "slack_ts")
    inlines = [SessionInline, RegistrationInline]
    actions = [send_slack_announcement]

    def get_urls(self):
        urls = super().get_urls()

        return [
            url(
                "export/resume/(?P<event_id>.*)",
                self.export_resumes,
                name="event_event_export_resumes",
            )
        ] + urls

    # TODO: Actually add a decorator to avoid people without permissions to access this
    def export_resumes(self, request, event_id):
        if request.user.is_authenticated and request.user.is_admin:
            resumes = get_event_resumes_zip(event_id=event_id)
            response = HttpResponse(resumes.getvalue(), content_type="application/zip")
            response[
                "Content-Disposition"
            ] = f'attachment; filename="event-{event_id}-resumes.zip"'
            return response

    def registration_count(self, obj):
        return (
            obj.registrations.filter(
                status__in=[
                    RegistrationStatus.REGISTERED,
                    RegistrationStatus.JOINED,
                    RegistrationStatus.ATTENDED,
                ]
            )
            .exclude(user__type=UserType.ORGANISER)
            .count()
        )

    def new_user_count(self, obj):
        return (
            obj.registrations.filter(
                status__in=[
                    RegistrationStatus.REGISTERED,
                    RegistrationStatus.JOINED,
                    RegistrationStatus.ATTENDED,
                ],
                created_at__gte=F("user__created_at") - timezone.timedelta(minutes=1),
                created_at__lte=F("user__created_at") + timezone.timedelta(minutes=1),
            )
            .exclude(user__type=UserType.ORGANISER)
            .count()
        )

    def diet_restrictions(self, obj):
        registrations = obj.registrations.all()
        diet_count = {dt: 0 for dt in DietType}
        diet_other = []
        for registration in registrations:
            for dt in registration.dietary_restrictions:
                diet_count[dt] += 1
            if registration.diet_other:
                diet_other.append(registration.diet_other)
        diet_html = "<ul style='margin-left: 0; padding-left: 0;'>"
        for dt, ct in diet_count.items():
            diet_html += f"<li>{DietType.labels[dt]}: {ct}</li>"
        diet_html += "</ul>"
        if diet_other:
            diet_html += "Other restrictions"
            for do in diet_other:
                diet_html += f"<br><span style='padding-left: 2em;'>- {do}</span>"
        return format_html(diet_html)

    registration_count.short_description = "registrations"
    new_user_count.short_description = "new users"
    diet_restrictions.short_description = "dietary restrictions"


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "surname", "email", "user")
    list_display = ("name", "surname", "email", "user")
    ordering = ("-created_at", "-updated_at", "name")
    readonly_fields = ("created_at",)
