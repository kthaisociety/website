from typing import List

from event.models import Event


def get_future_events() -> List[Event]:
    return list(set(Event.objects.published_future().order_by("sessions__starts_at")))[
        :3
    ]


def get_past_events() -> List[Event]:
    return list(set(Event.objects.published_past().order_by("-sessions__starts_at")))[
        :3
    ]


def get_events() -> List[Event]:
    return list(set(Event.objects.published().order_by("-created_at")))[:3]
