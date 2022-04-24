import slack
from slack.errors import SlackApiError

from app.enums import SlackError
from app.settings import SL_CHANNEL_WEBDEV, SL_TOKEN
from messaging.api.slack.message import send_error_message


def add(channel_id: str, message_id: str, emoji: str) -> bool:
    if SL_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_TOKEN)
        try:
            response = client.reactions_add(
                channel=channel_id, timestamp=message_id, name=emoji
            )
        except SlackApiError as e:
            if e.response.get("error") != "already_reacted":
                raise e
            response = e.response
        if not response.status_code == 200 or not response.data.get("ok", False):
            return send_error_message(error=SlackError.ADD_REACTION)
        return True
