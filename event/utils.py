from typing import List

from event.models import Event


def get_future_events() -> List[Event]:
    return Event.objects.published_future().order_by("starts_at")[:3]


def get_past_events() -> List[Event]:
    return Event.objects.published_past().order_by("-starts_at")[:3]
