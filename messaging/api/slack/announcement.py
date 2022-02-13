from typing import List
from uuid import UUID

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from app.settings import (
    SL_CHANNEL_GENERAL,
    APP_FULL_DOMAIN,
    SL_CHANNEL_EVENTS,
    SL_CHANNEL_ARTICLES,
    SL_CHANNEL_JOBS,
    SL_JOIN_EVENT,
)
from app.utils import get_full_url
from business.models import Offer
from event.models import Event
from messaging.api.slack import log, reaction
from messaging.api.slack.channel import send_message
from messaging.enums import LogType
from messaging.models import SlackChannel
from news.models import Article


@transaction.atomic
def announce_event(event: Event, creator_id: UUID):
    event_extra = (
        f":clock3: {timezone.localtime(event.starts_at).strftime('%B %-d, %Y %H:%M')}"
    )
    if event.location:
        event_extra += f"\n:round_pushpin: {event.location}"
    if event.is_signup_open:
        event_extra += f"\n:pencil: *<{APP_FULL_DOMAIN}{event.url}|Signup here>*{' or react with :' + SL_JOIN_EVENT + ':' if not event.collect_resume else '' }"
    if event.social_url:
        event_extra += (
            f"\n:facebook: Check out our *<{event.social_url}|Facebook event>*"
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
                "text": event_extra,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": event.description_paragraph,
            },
        },
        {
            "type": "image",
            "image_url": f"{APP_FULL_DOMAIN}{event.picture.url}",
            "alt_text": "Event picture",
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

    slack_ts = response.get("message")

    # TODO: Remove this update for model save
    # https://sentry.io/organizations/kth-ai-society/issues/3011067224
    Event.objects.filter(id=event.id).update(slack_ts=slack_ts)

    reaction.add(
        channel_id=channel.external_id, message_id=event.slack_ts, emoji=SL_JOIN_EVENT
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
                + f"\n\n:computer: Check it out in *<{get_full_url(article.url)}|our website>*",
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


def announce_job_offers(job_offers: List[Offer]):
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "emoji": True, "text": "New job offers"},
        },
    ]

    for job_offer in job_offers:
        offer_location = f"🖥️ {job_offer.company.name}, Remote"
        if job_offer.location:
            offer_location = f"🌍 {job_offer.company.name}, {job_offer.location}"
        blocks += [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{job_offer.title}*\n<{APP_FULL_DOMAIN}{job_offer.our_url}|*{offer_location}*>\n{job_offer.description_short}",
                },
                "accessory": {
                    "type": "image",
                    "image_url": f"{APP_FULL_DOMAIN}{job_offer.company.logo.url}",
                    "alt_text": job_offer.company.name,
                },
            }
        ]

    blocks += [
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Read more", "emoji": True},
                    "url": f"{APP_FULL_DOMAIN}{reverse('business_jobs')}",
                }
            ],
        }
    ]

    channel = SlackChannel.objects.get(
        external_id=SL_CHANNEL_JOBS or SL_CHANNEL_GENERAL
    )
    response = send_message(
        external_id=channel.external_id,
        blocks=blocks,
        unfurl_links=False,
        unfurl_media=False,
    )

    for job_offer in job_offers:
        log.create(
            type=LogType.JOB,
            target=job_offer,
            channel_id=channel.id,
            data=response.data,
        )
