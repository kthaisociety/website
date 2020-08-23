from django.db import models
from django.utils import timezone

from event.enums import EventStatus


class EventManager(models.Manager):
    def published(self):
        return super().get_queryset().filter(status=EventStatus.PUBLISHED)

    def future(self):
        return (
            super()
            .get_queryset()
            .filter(sessions__starts_at__gte=timezone.now().date())
        )

    def published_future(self):
        return (
            super()
            .get_queryset()
            .filter(
                status=EventStatus.PUBLISHED, sessions__starts_at__gte=timezone.now()
            )
        )

    def published_past(self):
        return (
            super()
            .get_queryset()
            .filter(status=EventStatus.PUBLISHED)
            .exclude(sessions__starts_at__lt=timezone.now().date())
        )


class SessionManager(models.Manager):
    def published(self):
        return super().get_queryset().filter(event__status=EventStatus.PUBLISHED)
