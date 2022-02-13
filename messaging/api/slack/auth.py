import slack
from django.urls import reverse

from app.enums import SlackError
from app.settings import SL_ID, SL_SECRET, APP_FULL_DOMAIN
from messaging.api.slack.message import send_error_message
from user.models import User


def auth(code: str, user: User) -> bool:
    client = slack.WebClient()
    response = client.oauth_v2_access(
        client_id=SL_ID,
        client_secret=SL_SECRET,
        code=code,
        redirect_uri=f"{APP_FULL_DOMAIN}{reverse('slack_user_auth')}",
    )
    if not response.status_code == 200 or not response.data.get("ok", False):
        return send_error_message(error=SlackError.ADD_MESSAGE)

    authed_user = response.data.get("authed_user")
    user.slack_id = authed_user.get("id")
    user.slack_token = authed_user.get("access_token")
    user.slack_scopes = authed_user.get("scope")
    user.save()

    return True
