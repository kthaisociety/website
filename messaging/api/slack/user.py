from io import BytesIO
from typing import Dict

import requests
from django.core.files import File

from app.enums import SlackError
from app.slack import send_error_message
from user.models import User


def update(user_data: Dict) -> bool:
    user_slack = user_data.get("user")
    user_slack_id = user_slack.get("id")
    user = User.objects.filter(slack_id=user_slack_id).first()
    if user:
        user_slack_profile = user_slack.get("profile")
        user.slack_id = user_slack_id
        if user_slack_profile:
            user.slack_status_text = user_slack_profile.get("status_text")
            user.slack_status_emoji = user_slack_profile.get("status_emoji")
            user.slack_display_name = user_slack_profile.get("display_name")

            user_slack_image_original = user_slack_profile.get("image_original")
            if user_slack_image_original:
                response = requests.get(user_slack_image_original)
                if response.status_code == 200:
                    file = BytesIO(response.content)
                    user.slack_picture.save(f"{user.id}.jpg", File(file), save=False)

            return user.save()

    return False


def create(user_data: Dict) -> bool:
    user_slack = user_data.get("user")
    user_slack_profile = user_slack.get("profile")
    user_slack_email = user_slack_profile.get("email")
    user_slack_name = user_slack_profile.get("real_name")
    user_slack_surname = " ".join(user_slack_name.split(" ")[1:])
    user_slack_name = user_slack_name.split(" ")[0]
    User.objects.create_participant_from_slack(email=user_slack_email, name=user_slack_name, surname=user_slack_surname)

    return update(user_data=user_data)
