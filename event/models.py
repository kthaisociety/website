import uuid

from django.db import models
from django.utils import timezone
from versatileimagefield.fields import VersatileImageField

from event.enums import EventType, EventStatus


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=31, unique=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    type = models.PositiveSmallIntegerField(
        choices=((t.value, t.name) for t in EventType),
        default=EventType.GENERAL
    )
    picture = VersatileImageField("Image", upload_to="event/picture/")
    status = models.PositiveSmallIntegerField(
        choices=((s.value, s.name) for s in EventStatus),
        default=EventStatus.DRAFT
    )
    location = models.CharField(max_length=255)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    signup_starts_at = models.DateTimeField(blank=True, null=True)
    signup_ends_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_event_running(self):
        return self.starts_at <= timezone.now() < self.ends_at

    @property
    def is_signup_open(self):
        if not self.signup_ends_at:
            return True
        elif timezone.now() > self.signup_ends_at:
            return False
        elif self.signup_starts_at:
            return timezone.now() >= self.signup_starts_at
        return False
