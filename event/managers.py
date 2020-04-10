from django.db import models
from django.utils import timezone

from event.enums import EventStatus


class EventManager(models.Manager):
    def published(self):
        return super().get_queryset().filter(status=EventStatus.PUBLISHED)

    def future(self):
        return super().get_queryset().filter(starts_at__date__gte=timezone.now().date())

    def published_future(self):
        return (
            super()
            .get_queryset()
            .filter(
                status=EventStatus.PUBLISHED, starts_at__date__gte=timezone.now().date()
            )
        )

    def published_past(self):
        return (
            super()
            .get_queryset()
            .filter(status=EventStatus.PUBLISHED)
            .exclude(starts_at__date__gte=timezone.now().date())
        )
