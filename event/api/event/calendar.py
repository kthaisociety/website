from typing import Optional, List

from django.db import transaction

import app.services.google.calendar
from event.enums import EventStatus
from event.models import Event, Session


@transaction.atomic
def create_or_update(event: Event):
    session_updates = []
    if event.status == EventStatus.PUBLISHED:
        for session in event.sessions.all():
            if session.google_id:
                app.services.google.calendar.create_or_update(session=session)
            else:
                google_response = app.services.google.calendar.create_or_update(session=session)
                session.google_id = google_response.get("id")
                session_updates.append(session)
    else:
        for session in event.sessions.all():
            if session.google_id:
                app.services.google.calendar.delete(google_id=session.google_id)

    Session.objects.bulk_update(session_updates, fields=("google_id",))


@transaction.atomic
def delete(google_ids: List[str]):
    for google_id in google_ids:
        app.services.google.calendar.delete(google_id=google_id)

