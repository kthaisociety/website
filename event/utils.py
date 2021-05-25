from typing import List

from event.models import Event


def get_future_events() -> List[Event]:
    return sorted(
        list(set(Event.objects.published_future())), key=lambda e: e.created_at
    )[:3]


def get_past_events() -> List[Event]:
    return sorted(
        list(set(Event.objects.published_past())),
        key=lambda e: e.created_at,
        reverse=True,
    )[:3]


def get_events() -> List[Event]:
    return sorted(
        list(set(Event.objects.published())), key=lambda e: e.created_at, reverse=True
    )[:3]
