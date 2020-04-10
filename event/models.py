import re
import textwrap
import uuid
from io import StringIO

from django_markup.markup import formatter

from app.variables import APP_NAME, APP_ATTENDANCE_RATIO

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify
from versatileimagefield.fields import VersatileImageField

from event.enums import EventType, EventStatus, RegistrationStatus
from event.managers import EventManager


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True, unique=True)
    description = models.TextField(blank=True, null=True)
    type = models.PositiveSmallIntegerField(
        choices=((t.value, t.name) for t in EventType), default=EventType.GENERAL
    )
    picture = VersatileImageField("Image", upload_to="event/picture/")
    status = models.PositiveSmallIntegerField(
        choices=((s.value, s.name) for s in EventStatus), default=EventStatus.DRAFT
    )
    location = models.CharField(max_length=255)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    signup_starts_at = models.DateTimeField(blank=True, null=True)
    signup_ends_at = models.DateTimeField(blank=True, null=True)
    attendance_target = models.IntegerField(blank=True, null=True)
    attendance_limit = models.IntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EventManager()

    @property
    def description_short(self):
        return textwrap.shorten(self.description, width=250, placeholder="...")

    @property
    def url(self):
        return reverse("events_event", kwargs=dict(code=self.code))

    @property
    def ics_url(self):
        return reverse("events_event_ics", kwargs=dict(code=self.code))

    @property
    def ics(self):
        description = formatter(self.description, "markup")
        description_text = (
            re.sub("[ \t]+", " ", strip_tags(description)).replace("\n ", "\n").strip()
        )
        with StringIO() as icsfile:
            icsfile.write("BEGIN:VCALENDAR\n")
            icsfile.write("VERSION:2.0\n")
            icsfile.write(f"PRODID:-//{reverse('app_home')}//{APP_NAME}\n")
            icsfile.write("CALSCALE:GREGORIAN\n")
            icsfile.write("BEGIN:VEVENT\n")
            icsfile.write(f"SUMMARY:{self.name}\n")
            icsfile.write(f"DTSTART:{self.starts_at.strftime('%Y%m%dT%H%M%SZ')}\n")
            icsfile.write(f"DTEND:{self.ends_at.strftime('%Y%m%dT%H%M%SZ')}\n")
            icsfile.write(
                f"UID:kthais-{self.starts_at.strftime('%Y%m%d')}-{self.code}\n"
            )
            icsfile.write(f"DTSTAMP:{timezone.now().strftime('%Y%m%dT%H%M%SZ')}\n")
            icsfile.write(f"LOCATION:{self.location}\n")
            icsfile.write(f"DESCRIPTION:{description_text}\n")
            # icsfile.write("STATUS:CONFIRMED\n")
            icsfile.write("SEQUENCE:3\n")
            icsfile.write("END:VEVENT\n")
            icsfile.write("END:VCALENDAR\n")
            return icsfile.getvalue()

    @property
    def is_event_running(self):
        return self.starts_at <= timezone.now() < self.ends_at

    @property
    def is_signup_open(self):
        if timezone.now() > self.ends_at:
            return False
        elif not self.signup_ends_at:
            return True
        elif timezone.now() > self.signup_ends_at:
            return False
        elif self.signup_starts_at:
            return timezone.now() >= self.signup_starts_at
        return False

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        if self.attendance_target and not self.attendance_limit:
            self.attendance_limit = APP_ATTENDANCE_RATIO * self.attendance_target
        super().save()

    def __str__(self):
        return self.name


class Registration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        "event.Event", on_delete=models.PROTECT, related_name="registrations"
    )
    user = models.ForeignKey(
        "user.User", on_delete=models.PROTECT, related_name="registrations"
    )
    status = models.PositiveSmallIntegerField(
        choices=((s.value, s.name) for s in RegistrationStatus),
        default=RegistrationStatus.REQUESTED,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
