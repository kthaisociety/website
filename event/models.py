import re
import textwrap
import uuid
from io import StringIO
from typing import Optional

import markdown
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify
from versatileimagefield.fields import VersatileImageField

from app.storage import OverwriteStorage
from app.variables import APP_ATTENDANCE_RATIO, APP_NAME
from event.enums import (
    AttachmentStatus,
    AttachmentType,
    EventStatus,
    EventType,
    RegistrationStatus,
    ScheduleType,
    SignupStatus,
    SpeakerRoleType,
    StreamingProvider,
)
from event.managers import EventManager, SessionManager
from user.enums import DietType


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True, unique=True)
    description = models.TextField(blank=True, null=True)
    type = models.PositiveSmallIntegerField(
        choices=((t.value, t.name) for t in EventType), default=EventType.GENERAL
    )
    external_url = models.CharField(max_length=255, blank=True, null=True)
    picture = VersatileImageField("Image", upload_to="event/picture/")
    social_picture = VersatileImageField(
        "Social image", blank=True, null=True, upload_to="event/social/"
    )
    social_url = models.URLField(max_length=200, blank=True, null=True)
    status = models.PositiveSmallIntegerField(
        choices=((s.value, s.name) for s in EventStatus), default=EventStatus.DRAFT
    )
    location = models.CharField(max_length=255, blank=True, null=True)
    signup_starts_at = models.DateTimeField(blank=True, null=True)
    signup_ends_at = models.DateTimeField(blank=True, null=True)
    signup_url = models.URLField(max_length=200, blank=True, null=True)
    account_required = models.BooleanField(default=False)
    registration_available = models.BooleanField(default=True)
    attendance_target = models.IntegerField(blank=True, null=True)
    attendance_limit = models.IntegerField(blank=True, null=True)

    # Dietary restrictions
    has_food = models.BooleanField(default=False)

    # Resume collection
    collect_resume = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Slack Timestamp
    # The size is not explained in the original docs:
    # https://api.slack.com/apis/connections/events-api#the-events-api__receiving-events__event-type-structure
    slack_ts = models.CharField(max_length=255, blank=True, null=True)

    objects = EventManager()

    @property
    def starts_at(self) -> Optional[timezone.datetime]:
        session = self.sessions.all().order_by("starts_at").first()
        if session:
            return session.starts_at
        return None

    @property
    def ends_at(self) -> Optional[timezone.datetime]:
        session = self.sessions.all().order_by("-ends_at").first()
        if session:
            return session.ends_at
        return None

    @property
    def registration_ends_at(self) -> Optional[timezone.datetime]:
        return self.signup_ends_at or self.ends_at

    @property
    def streaming_provider(self) -> Optional[StreamingProvider]:
        if self.type == EventType.WEBINAR and self.external_url:
            pre_domain = r"((http|https):\/\/)([a-zA-Z0-9\-]+\.)*"
            post_domain = r"\..*"
            if re.match(rf"^{pre_domain}meet{post_domain}$", self.external_url):
                return StreamingProvider.GOOGLE_MEET
            if re.match(rf"^{pre_domain}youtube{post_domain}$", self.external_url):
                return StreamingProvider.YOUTUBE
            if re.match(rf"^{pre_domain}zoom{post_domain}$", self.external_url):
                return StreamingProvider.ZOOM
        return None

    @property
    def description_plaintext(self):
        html = markdown.markdown(self.description)
        return "".join(BeautifulSoup(html, "html.parser").findAll(text=True))

    @property
    def description_extra_short(self):
        return textwrap.shorten(
            self.description_plaintext, width=125, placeholder="..."
        )

    @property
    def description_short(self):
        return textwrap.shorten(
            self.description_plaintext, width=250, placeholder="..."
        )

    @property
    def description_paragraph(self):
        return self.description_plaintext.partition("\n")[0]

    @property
    def url(self):
        return reverse("events_event", kwargs=dict(code=self.code))

    @property
    def ics_url(self):
        return reverse("events_event_ics", kwargs=dict(code=self.code))

    @property
    def ics(self):
        description = markdown.markdown(self.description)
        description_text = (
            re.sub("[ \t]+", " ", strip_tags(description)).replace("\n ", "\n").strip()
        )
        with StringIO() as icsfile:
            icsfile.write("BEGIN:VCALENDAR\n")
            icsfile.write("VERSION:2.0\n")
            icsfile.write(f"PRODID:-//{reverse('app_home')}//{APP_NAME}\n")
            icsfile.write("CALSCALE:GREGORIAN\n")
            if self.starts_at and self.ends_at:
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
    def is_event_running(self) -> bool:
        return (
            self.starts_at
            and self.ends_at
            and self.starts_at <= timezone.now() < self.ends_at
        )

    @property
    def is_event_future(self) -> bool:
        return self.ends_at and timezone.now() < self.ends_at

    @property
    def is_signup_open(self) -> bool:
        return self.signup_status == SignupStatus.OPEN

    @property
    def signup_status(self) -> SignupStatus:
        if self.ends_at and timezone.now() > self.ends_at:
            return SignupStatus.PAST
        elif self.is_signup_full:
            return SignupStatus.FULL
        elif not self.signup_ends_at:
            return SignupStatus.OPEN
        elif timezone.now() > self.signup_ends_at:
            return SignupStatus.PAST
        elif self.signup_starts_at:
            if timezone.now() >= self.signup_starts_at:
                return SignupStatus.OPEN
            return SignupStatus.FUTURE
        return SignupStatus.CLOSED

    @property
    def is_signup_full(self):
        if self.attendance_limit is not None:
            return (
                Registration.objects.filter(
                    event_id=self.id,
                    status__in=[
                        RegistrationStatus.REQUESTED,
                        RegistrationStatus.REGISTERED,
                    ],
                ).count()
                >= self.attendance_limit
            )
        return False

    @property
    def social(self):
        if self.social_picture:
            return self.social_picture
        return self.picture

    def clean(self):
        messages = {}
        if self.type != EventType.WEBINAR:
            if not self.location:
                messages[
                    "location"
                ] = "The location is mandatory for non-WEBINAR events."
        if messages:
            raise ValidationError(messages)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        if self.attendance_target and not self.attendance_limit:
            self.attendance_limit = APP_ATTENDANCE_RATIO * self.attendance_target

        import event.api.event.calendar

        transaction.on_commit(
            lambda: event.api.event.calendar.create_or_update(event=self)
        )

        super().save()

    def delete(self, *args, **kwargs):
        import event.api.event.calendar

        transaction.on_commit(
            lambda: event.api.event.calendar.delete(
                google_ids=[
                    session.google_id
                    for session in self.sessions.all()
                    if session.google_id
                ]
            )
        )

        super().delete()

    def __str__(self):
        return self.name


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    event = models.ForeignKey(
        "Event", on_delete=models.PROTECT, related_name="sessions"
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    google_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SessionManager()

    @property
    def published_attachments(self):
        return self.attachments.filter(
            status=AttachmentStatus.PUBLISHED, registration_required=False
        )

    @property
    def published_attachments_with_registration(self):
        return self.attachments.filter(status=AttachmentStatus.PUBLISHED)

    def save(self, *args, **kwargs):
        import event.api.event.calendar

        transaction.on_commit(
            lambda: event.api.event.calendar.create_or_update(event=self.event)
        )

        super().save()

    def delete(self, *args, **kwargs):
        import event.api.event.calendar

        if self.google_id:
            transaction.on_commit(
                lambda: event.api.event.calendar.delete(google_ids=[self.google_id])
            )

        super().delete()

    def __str__(self):
        return f"{self.event.name} - {self.name}"


class Schedule(models.Model):
    name = models.CharField(max_length=255)
    session = models.ForeignKey(
        "Session", on_delete=models.PROTECT, related_name="schedules"
    )
    type = models.PositiveSmallIntegerField(
        choices=((t.value, t.name) for t in ScheduleType), default=ScheduleType.GENERAL
    )
    place = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(max_length=1000, blank=True, null=True)

    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.session.event.name} - {self.session.name} - {self.name}"

    def clean(self):
        # TODO: Check if more than one EVENT_START and EVENT_END
        messages = {}
        if not self.session.starts_at <= self.starts_at <= self.session.ends_at:
            messages["starts_at"] = "The start time must be inside the session times."
        if (
            self.ends_at
            and not self.session.starts_at <= self.ends_at <= self.session.ends_at
        ):
            messages["ends_at"] = "The end time must be inside the session times."
        if messages:
            raise ValidationError(messages)


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

    # Dietary restrictions
    diet = models.CharField(max_length=255, blank=True, null=True)
    diet_other = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active(self):
        return self.status not in [
            RegistrationStatus.REQUESTED,
            RegistrationStatus.INTERESTED,
            RegistrationStatus.WAIT_LISTED,
            RegistrationStatus.CANCELLED,
        ]

    @property
    def dietary_restrictions(self):
        if not self.diet:
            return []
        diets = re.sub(r"[^0-9,]", "", self.diet).split(",")
        diet_types = set()
        for diet in diets:
            if diet != "":
                diet_types.add(DietType(int(diet)))
        return diet_types

    def __str__(self):
        return f"{self.event.name} - {self.user}"

    class Meta:
        unique_together = ("event", "user")


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    session = models.ForeignKey(
        "event.Session", on_delete=models.PROTECT, related_name="attachments"
    )
    type = models.PositiveSmallIntegerField(
        choices=((t.value, t.name) for t in AttachmentType),
        default=AttachmentType.SLIDES,
    )
    file = models.FileField(upload_to="event/attachment/file/", blank=True, null=True)
    external_url = models.CharField(max_length=255, blank=True, null=True)
    preview = VersatileImageField("Image", upload_to="event/attachment/preview/")
    status = models.PositiveSmallIntegerField(
        choices=((s.value, s.name) for s in AttachmentStatus),
        default=AttachmentStatus.DRAFT,
    )
    registration_required = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def url(self):
        if self.file:
            return self.file.url
        return self.external_url

    def __str__(self):
        return f"{self.session.event.name} - {self.name}"


class Speaker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(verbose_name="First name", max_length=255)
    surname = models.CharField(verbose_name="Last name", max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(
        "user.User",
        on_delete=models.PROTECT,
        related_name="speakers",
        blank=True,
        null=True,
    )
    picture = VersatileImageField(
        "Image",
        upload_to="event/speaker/picture/",
        default="event/speaker/picture/profile.png",
        storage=OverwriteStorage(),
    )
    website = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)

    description = models.TextField(max_length=5000, blank=True, null=True)

    # Social networks
    linkedin_url = models.URLField(max_length=200, blank=True, null=True)
    twitter_url = models.URLField(max_length=200, blank=True, null=True)
    scholar_url = models.URLField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        if self.surname:
            return self.name + " " + self.surname
        return self.name

    def __str__(self):
        if self.email:
            return f"{self.full_name} <{self.email}>"
        return self.full_name


class SpeakerRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    speaker = models.ForeignKey(
        "event.Speaker", on_delete=models.PROTECT, related_name="roles"
    )
    session = models.ForeignKey(
        "event.Session", on_delete=models.PROTECT, related_name="roles"
    )
    type = models.PositiveSmallIntegerField(
        choices=((srt.value, srt.name) for srt in SpeakerRoleType),
        default=SpeakerRoleType.SPEAKER,
    )
