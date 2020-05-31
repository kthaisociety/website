from typing import List

from event.models import Event, Registration


def get_future_events() -> List[Event]:
    return list(set(Event.objects.published_future().order_by("sessions__starts_at")))[
        :3
    ]


def get_past_events() -> List[Event]:
    return list(set(Event.objects.published_past().order_by("-sessions__starts_at")))[
        :3
    ]


def get_user_registrations(user_id: int) -> List[Registration]:
    return Registration.objects.filter(user_id=user_id).order_by("-created_at")
