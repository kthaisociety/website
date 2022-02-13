import datetime
from typing import List, Dict, Optional

import slack
from django.db import transaction
from django.utils import timezone
from slack.errors import SlackApiError
from slack.web.slack_response import SlackResponse

from app.enums import SlackError
from app.settings import SL_TOKEN, SL_CHANNEL_WEBDEV, SL_USER_TOKEN
from messaging.api.slack.message import send_error_message
from messaging.models import SlackChannel
from user.models import User


def create_slack_channel(slack_channel: Dict) -> SlackChannel:
    return SlackChannel.objects.update_or_create(
        name=slack_channel.get("name"),
        defaults={
            "external_id": slack_channel.get("id"),
            "is_general": slack_channel.get("is_general"),
            "is_archived": slack_channel.get("is_archived"),
            "is_private": slack_channel.get("is_private"),
            "topic": slack_channel.get("topic", {}).get("value"),
            "purpose": slack_channel.get("purpose", {}).get("value"),
            "num_members": slack_channel.get("num_members", 0),
            "external_creator_id": slack_channel.get("creator"),
            "external_created_at": (
                timezone.make_aware(
                    datetime.datetime.fromtimestamp(slack_channel.get("created"))
                )
                if slack_channel.get("created")
                else timezone.now()
            ),
        },
    )[0]


@transaction.atomic
def retrieve_all() -> List[SlackChannel]:
    if SL_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_TOKEN)
        response = client.conversations_list()
        if not response.status_code == 200 or not response.data.get("ok", False):
            return send_error_message(error=SlackError.RETRIEVE_CHANNELS)

        slack_channels = []
        for slack_channel in response.data["channels"]:
            # Filter only public channels
            if (
                slack_channel.get("is_channel", False)
                and not slack_channel.get("is_private", True)
                and not slack_channel.get("is_archived", True)
            ):
                slack_channels.append(create_slack_channel(slack_channel=slack_channel))
                client.conversations_join(channel=slack_channel.get("id"))

        channels = list(SlackChannel.objects.all())
        current_channel_ids = [s.id for s in slack_channels]
        channel_ids_to_delete = [
            c.id for c in channels if c.id not in current_channel_ids
        ]
        SlackChannel.objects.filter(id__in=channel_ids_to_delete).delete()

        return slack_channels


@transaction.atomic
def retrieve(external_id: str) -> Optional[SlackChannel]:
    if SL_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_TOKEN)
        response = client.conversations_info(
            channel=external_id, include_num_members=True
        )
        if not response.status_code == 200 or not response.data.get("ok", False):
            return send_error_message(error=SlackError.RETRIEVE_CHANNEL)

        channel = None
        slack_channel = response.data["channel"]
        # Filter only public channels
        if slack_channel.get("is_channel", False) and not slack_channel.get(
            "is_private", True
        ):
            channel = create_slack_channel(slack_channel=slack_channel)
            client.conversations_join(channel=slack_channel.get("id"))

        return channel


def set_name(external_id: str, name: str) -> bool:
    if SL_USER_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_USER_TOKEN)
        response = client.conversations_rename(channel=external_id, name=name)
        if not response.status_code == 200 or not response.data.get("ok", False):
            return send_error_message(error=SlackError.SET_CHANNEL_NAME)
        return True


def set_topic(external_id: str, topic: str) -> bool:
    if SL_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_TOKEN)
        response = client.conversations_setTopic(channel=external_id, topic=topic)
        if not response.status_code == 200 or not response.data.get("ok", False):
            return send_error_message(error=SlackError.SET_CHANNEL_TOPIC)
        return True


def set_purpose(external_id: str, purpose: str) -> bool:
    if SL_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_TOKEN)
        response = client.conversations_setPurpose(channel=external_id, purpose=purpose)
        if not response.status_code == 200 or not response.data.get("ok", False):
            return send_error_message(error=SlackError.SET_CHANNEL_PURPOSE)
        return True


@transaction.atomic
def invite_users(external_id: str) -> bool:
    if SL_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_TOKEN)
        user_slack_ids = list(
            User.objects.slack_active().values_list("slack_id", flat=True)
        )
        try:
            response = client.conversations_invite(
                channel=external_id, users=user_slack_ids
            )
        except SlackApiError as e:
            if e.response.get("error") != "already_in_channel":
                raise e
            response = e.response
        users_already = [
            error.get("user")
            for error in response.data.get("errors", [])
            if error.get("error") == "already_in_channel"
        ]
        # If there was someone not already the "ok" will already be True,
        # otherwise check only "already in channel errors" were produced
        if (
            not response.status_code == 200 or not response.data.get("ok", False)
        ) and len(user_slack_ids) != len(users_already):
            return send_error_message(error=SlackError.INVITE_CHANNEL_USERS)

        # Update channel information
        retrieve(external_id=external_id)

        return True


@transaction.atomic
def create(
    name: str, topic: Optional[str] = None, purpose: Optional[str] = None
) -> bool:
    if SL_TOKEN and SL_USER_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_USER_TOKEN)
        response = client.conversations_create(name=name)
        if not response.status_code == 200 or not response.data.get("ok", False):
            return send_error_message(error=SlackError.CREATE_CHANNEL)

        slack_channel = response.data.get("channel")
        slack_channel["topic"] = {"value": topic}
        slack_channel["purpose"] = {"value": purpose}
        channel = create_slack_channel(slack_channel=slack_channel)

        client_bot = slack.WebClient(SL_TOKEN)
        client_bot.conversations_join(channel=slack_channel.get("id"))

        if topic:
            set_topic(external_id=channel.external_id, topic=topic)

        if purpose:
            set_purpose(external_id=channel.external_id, purpose=purpose)

        return True


@transaction.atomic
def send_message(
    external_id: str, blocks: List, unfurl_links: bool = True, unfurl_media: bool = True
) -> SlackResponse:
    if SL_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_TOKEN)
        response = client.chat_postMessage(
            channel=external_id,
            blocks=blocks,
            unfurl_links=unfurl_links,
            unfurl_media=unfurl_media,
        )
        if not response.status_code == 200 or not response.data.get("ok", False):
            send_error_message(error=SlackError.SET_CHANNEL_TOPIC)
        return response


@transaction.atomic
def update_message(
    external_id: str,
    message_ts: str,
    blocks: List,
    unfurl_links: bool = True,
    unfurl_media: bool = True,
) -> SlackResponse:
    if SL_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_TOKEN)
        response = client.chat_update(
            channel=external_id,
            ts=message_ts,
            blocks=blocks,
            unfurl_links=unfurl_links,
            unfurl_media=unfurl_media,
        )
        if not response.status_code == 200 or not response.data.get("ok", False):
            send_error_message(error=SlackError.SET_CHANNEL_TOPIC)
        return response
