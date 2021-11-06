from typing import Dict

from app.settings import (
    SL_ID,
    SL_EMOJI_BOT,
    SL_ANSWER_BOT,
    SL_CHANNEL_EVENTS,
    SL_CHANNEL_GENERAL,
    SL_JOIN_EVENT,
)
from messaging.api.slack import reaction, channel, chat, user, events


def run(body: Dict) -> bool:
    event_type = body.get("type")
    success = True
    if event_type == "app_mention":
        channel_id = body.get("channel")
        message_id = body.get("ts")
        emoji = SL_EMOJI_BOT
        text = SL_ANSWER_BOT
        if channel_id and message_id and emoji and text:
            if not reaction.add(
                channel_id=channel_id, message_id=message_id, emoji=emoji
            ) or not chat.post(channel_id=channel_id, message_id=message_id, text=text):
                success = False
    elif event_type.startswith("channel"):
        channel.retrieve_all()
    elif event_type == "user_change":
        if not user.update(user_data=body.get("user")):
            success = False
        pass
    elif event_type in ["member_joined_channel", "member_left_channel"]:
        channel_id = body.get("channel")
        if not channel.retrieve(external_id=channel_id):
            success = False
    elif event_type == "reaction_added":
        channel_id = body.get("item").get("channel")
        reaction_id = body.get("reaction")
        user_id = body.get("user")

        if (
            reaction_id == SL_JOIN_EVENT
            and body.get("item_user") == SL_ID
            and channel_id in [SL_CHANNEL_EVENTS, SL_CHANNEL_GENERAL]
        ):
            events.join_event(user_id=user_id, event_ts=body.get("item").get("ts"))

    elif event_type == "reaction_removed":
        channel_id = body.get("item").get("channel")
        reaction_id = body.get("reaction")
        user_id = body.get("user")

        if (
            reaction_id == SL_JOIN_EVENT
            and body.get("item_user") == SL_ID
            and channel_id in [SL_CHANNEL_EVENTS, SL_CHANNEL_GENERAL]
        ):
            events.leave_event(user_id=user_id, event_ts=body.get("item").get("ts"))
    return success
