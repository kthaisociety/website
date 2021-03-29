from uuid import UUID

from app.settings import SL_CHANNEL_GENERAL, APP_FULL_DOMAIN, SL_CHANNEL_EVENTS, SL_CHANNEL_ARTICLES
from event.models import Event
from messaging.api.slack import log
from messaging.api.slack.channel import send_message
from messaging.enums import LogType
from messaging.models import SlackChannel
from news.models import Article


def announce_event(event: Event, user_id: UUID):
    event_extra = f":clock3: {event.starts_at.strftime('%B %-d, %Y %H:%M')}\n"
    if event.location:
        event_extra += f":round_pushpin: {event.location}\n"
    if event.is_signup_open:
        event_extra += (
            f":pencil: Make sure to *<{APP_FULL_DOMAIN}{event.url}|signup here>*\n"
        )
    if event.social_url:
        event_extra += (
            f":facebook: Checkout our *<{event.social_url}|Facebook event>*\n"
        )

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "emoji": True, "text": event.name},
        },
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "emoji": True,
                "text": event.description_paragraph,
            },
            "accessory": {
                "type": "image",
                "image_url": f"{APP_FULL_DOMAIN}{event.picture.url}",
                "alt_text": "Event picture",
            },
        },
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": event_extra}},
    ]

    channel = SlackChannel.objects.get(external_id=SL_CHANNEL_EVENTS or SL_CHANNEL_GENERAL)
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
        user_id=user_id,
        data=response.data,
    )


def announce_article(article: Article, user_id: UUID):
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "emoji": True, "text": article.title},
        },
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "emoji": True,
                "text": article.description_paragraph,
            },
            "accessory": {
                "type": "image",
                "image_url": f"{APP_FULL_DOMAIN}{article.picture.url}",
                "alt_text": "Article picture",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":computer: Check it out in *<{APP_FULL_DOMAIN}{article.url}|our website>*\n",
            },
        },
    ]

    channel = SlackChannel.objects.get(external_id=SL_CHANNEL_ARTICLES or SL_CHANNEL_GENERAL)
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
        user_id=user_id,
        data=response.data,
    )
