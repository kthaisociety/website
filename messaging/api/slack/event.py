from typing import Dict

from app.settings import SL_EMOJI_BOT, SL_ANSWER_BOT
from messaging.api.slack import reaction, channel, chat, user


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
    return success
