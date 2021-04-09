from uuid import UUID

from django.utils import timezone

from app.settings import (
    SL_CHANNEL_GENERAL,
    APP_FULL_DOMAIN,
    SL_CHANNEL_EVENTS,
    SL_CHANNEL_ARTICLES,
)
from event.models import Event
from messaging.api.slack import log
from messaging.api.slack.channel import send_message
from messaging.enums import LogType
from messaging.models import SlackChannel
from news.models import Article


def announce_event(event: Event, creator_id: UUID):
    event_extra = f":clock3: {timezone.localtime(event.starts_at).strftime('%B %-d, %Y %H:%M')}"
    if event.location:
        event_extra += f"\n:round_pushpin: {event.location}"
    if event.is_signup_open:
        event_extra += (
            f"\n:pencil: Make sure to *<{APP_FULL_DOMAIN}{event.url}|signup here>*"
        )
    if event.social_url:
        event_extra += (
            f"\n:facebook: Checkout our *<{event.social_url}|Facebook event>*"
        )

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "emoji": True, "text": event.name},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": event.description_paragraph + "\n\n" + event_extra,
            },
            "accessory": {
                "type": "image",
                "image_url": f"{APP_FULL_DOMAIN}{event.picture.url}",
                "alt_text": "Event picture",
            },
        },
    ]

    channel = SlackChannel.objects.get(
        external_id=SL_CHANNEL_EVENTS or SL_CHANNEL_GENERAL
    )
    response = send_message(
        external_id=channel.external_id,
        blocks=blocks,
        unfurl_links=False,
        unfurl_media=False,
    )

    log.create(
        type=LogType.EVENT,
        target=event,
        channel_id=channel.id,
        creator_id=creator_id,
        data=response.data,
    )


def announce_article(article: Article, creator_id: UUID):
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "emoji": True, "text": article.title},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": article.description_paragraph
                + f"\n\n:computer: Check it out in *<{APP_FULL_DOMAIN}{article.url}|our website>*",
            },
            "accessory": {
                "type": "image",
                "image_url": f"{APP_FULL_DOMAIN}{article.picture.url}",
                "alt_text": "Article picture",
            },
        },
    ]

    channel = SlackChannel.objects.get(
        external_id=SL_CHANNEL_ARTICLES or SL_CHANNEL_GENERAL
    )
    response = send_message(
        external_id=channel.external_id,
        blocks=blocks,
        unfurl_links=False,
        unfurl_media=False,
    )

    log.create(
        type=LogType.ARTICLE,
        target=article,
        channel_id=channel.id,
        creator_id=creator_id,
        data=response.data,
    )
