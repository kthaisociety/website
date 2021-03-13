from typing import Optional

import slack

from app.enums import SlackError
from app.settings import SL_TOKEN, SL_CHANNEL_WEBDEV
from app.slack import send_error_message


def post(channel_id: str, text: str, message_id: Optional[str] = None) -> bool:
    if SL_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_TOKEN)
        response = client.chat_postMessage(channel=channel_id, thread_ts=message_id, text=text)
        if not response.status_code == 200 or not response.data.get("ok", False):
            return send_error_message(error=SlackError.ADD_MESSAGE)
        return True
