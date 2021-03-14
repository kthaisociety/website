import os
from io import BytesIO
from typing import Dict

import requests
import slack
from PIL import Image
from django.core.files import File
from django.utils import timezone

from app.enums import SlackError
from app.settings import STATIC_ROOT
from app.slack import send_error_message
from user.models import User
from user.utils import send_created


# TODO: Set picture as well when updated through the website
def get_profile_picture(file: BytesIO) -> BytesIO:
    picture = Image.open(file).resize(size=(1024, 1024))
    mask = Image.open(os.path.join(STATIC_ROOT, "img/mask.png"))
    picture.paste(mask, (0, 0), mask=mask)
    new_file = BytesIO()
    picture.save(new_file, format="JPEG")
    return new_file


def set_picture(token: str, file: BytesIO) -> bool:
    client = slack.WebClient(token)
    response = client.users_setPhoto(image=file.read())
    if not response.status_code == 200 or not response.data.get("ok", False):
        return send_error_message(error=SlackError.RETRIEVE_CHANNELS)
    return True


def update(user_data: Dict) -> bool:
    user_slack_profile = user_data.get("profile")
    user_slack_email = user_slack_profile.get("email")
    user = User.objects.filter(
        email=user_slack_email,
        updated_at__lt=timezone.now() - timezone.timedelta(minutes=2),
    ).first()
    profile_picture_updated = False
    success = True
    if user:
        user.slack_id = user_data.get("id")
        user.slack_status_text = user_slack_profile.get("status_text")
        user.slack_status_emoji = user_slack_profile.get("status_emoji")
        user.slack_display_name = user_slack_profile.get("display_name")

        user_slack_image_original = user_slack_profile.get("image_original")
        user_slack_image_hash = user_slack_profile.get("avatar_hash")
        # Update the profile picture only if it changed
        if (
            user_slack_image_hash != user.slack_picture_hash
            and user_slack_image_original
        ):
            response = requests.get(user_slack_image_original)
            if response.status_code == 200:
                profile_picture_file = BytesIO(response.content)
                user.picture.save(
                    f"{user.id}.jpg", File(profile_picture_file), save=False
                )
                if user.is_organiser:
                    profile_picture_file = get_profile_picture(
                        file=profile_picture_file
                    )
                    profile_picture_updated = True
                user.slack_picture.save(
                    f"{user.id}.jpg", File(profile_picture_file), save=False
                )
        user.slack_picture_hash = user_slack_image_hash
        user.updated_at = timezone.now()

        user.save()

        if profile_picture_updated and user.slack_token:
            if not set_picture(
                token=user.slack_token, file=BytesIO(user.slack_picture.file.read())
            ):
                success = False

        return success
    return False


def create(user_data: Dict) -> bool:
    user_slack_profile = user_data.get("profile")
    user_slack_email = user_slack_profile.get("email")
    user_slack_name = user_slack_profile.get("real_name")
    user_slack_surname = " ".join(user_slack_name.split(" ")[1:])
    user_slack_name = user_slack_name.split(" ")[0]
    user = User.objects.create_participant_from_slack(
        email=user_slack_email, name=user_slack_name, surname=user_slack_surname
    )
    user.email_verified = True
    user.save()
    success = True

    success &= update(user_data=user_data)
    send_created(user)

    return success
