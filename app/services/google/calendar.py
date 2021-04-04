from typing import Dict, Optional

from googleapiclient.discovery import build

from app.settings import (
    GOOGLE_CALENDAR_CREDS,
    GOOGLE_CALENDAR_TEAM_ID,
    GOOGLE_CALENDAR_TEAM_EMAIL,
    APP_FULL_DOMAIN, GOOGLE_CALENDAR_ADMIN_EMAIL,
)
from event.models import Session


def create_or_update(session: Session) -> Dict:
    if not GOOGLE_CALENDAR_CREDS or not GOOGLE_CALENDAR_TEAM_ID or not GOOGLE_CALENDAR_ADMIN_EMAIL:
        return {}

    service = build("calendar", "v3", credentials=GOOGLE_CALENDAR_CREDS)

    if session.ends_at <= session.starts_at:
        return {}

    event_body = {
        "summary": session.name,
        "start": {"dateTime": session.starts_at.isoformat()},
        "end": {"dateTime": session.ends_at.isoformat()},
        "description": session.event.description_paragraph,
        "status": "confirmed",
        "transparency": "transparent",
        "visibility": "public",
        "source": {
            "title": session.event.name,
            "url": f"{APP_FULL_DOMAIN}{session.event.url}",
        },
    }

    if GOOGLE_CALENDAR_TEAM_EMAIL:
        event_body["attendees"] = [{"email": GOOGLE_CALENDAR_TEAM_EMAIL}]

    if session.event.location:
        event_body["location"] = session.event.location

    if session.google_id:
        return (
            service.events()
            .update(
                calendarId=GOOGLE_CALENDAR_TEAM_ID,
                eventId=session.google_id,
                sendUpdates="none",
                supportsAttachments=False,
                body=event_body,
            )
            .execute()
        )

    return (
        service.events()
        .insert(
            calendarId=GOOGLE_CALENDAR_TEAM_ID,
            sendUpdates="none",
            supportsAttachments=False,
            body=event_body,
        )
        .execute()
    )


def delete(google_id: str) -> Dict:
    if not GOOGLE_CALENDAR_CREDS or not GOOGLE_CALENDAR_TEAM_ID or not GOOGLE_CALENDAR_ADMIN_EMAIL:
        return {}

    service = build("calendar", "v3", credentials=GOOGLE_CALENDAR_CREDS)

    return (
        service.events()
        .delete(calendarId=GOOGLE_CALENDAR_TEAM_ID, eventId=google_id)
        .execute()
    )
