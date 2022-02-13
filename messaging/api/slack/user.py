import copy
import os
import time
from io import BytesIO
from typing import Dict, Tuple, Optional
from uuid import UUID

import requests
import slack
from PIL import Image, ImageChops
from django.core.files import File
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

import app.slack
import messaging.api.slack.message
from app.enums import SlackError
from app.settings import STATIC_ROOT, APP_FULL_DOMAIN
from messaging.api.slack import log
import messaging.api.slack.channel
from messaging.consts import WARNING_TIME_DAYS
from messaging.enums import LogType
from user.models import User
from user.utils import send_created


# TODO: Set picture as well when updated through the website
def get_profile_picture(file: BytesIO) -> BytesIO:
    original_picture = Image.open(file).resize(size=(1024, 1024))
    picture = Image.new("RGBA", original_picture.size)
    picture.paste(original_picture)
    mask = Image.open(os.path.join(STATIC_ROOT, "img/mask.png")).resize(
        size=(1024, 1024)
    )
    picture.paste(mask, (0, 0), mask=mask)
    final_picture = Image.new("RGB", picture.size)
    final_picture.paste(picture)
    new_file = BytesIO()
    final_picture.save(new_file, format="JPEG")
    return new_file


def set_picture(token: str, file: BytesIO) -> Tuple[bool, Optional[str]]:
    client = slack.WebClient(token)
    response = client.users_setPhoto(image=file.read())
    if not response.status_code == 200 or not response.data.get("ok", False):
        return messaging.api.slack.message.send_error_message(error=SlackError.SET_USER_PICTURE), None
    return True, response.data.get("profile", {}).get("avatar_hash")


def same_image(file_1, file_2):
    image_1 = Image.open(file_1)
    image_2 = Image.open(file_2)

    if image_1.height != image_2.height or image_1.width != image_2.width:
        return False

    if image_1.mode == image_2.mode == "RGBA":
        img1_alphas = [pixel[3] for pixel in image_1.getdata()]
        img2_alphas = [pixel[3] for pixel in image_2.getdata()]
        has_equal_alphas = img1_alphas == img2_alphas
    else:
        has_equal_alphas = True

    content = list(
        ImageChops.difference(image_1.convert("RGB"), image_2.convert("RGB")).getdata()
    )
    content_avg = (
        sum(
            [
                sum([c[0] for c in content]) / len(content),
                sum([c[1] for c in content]) / len(content),
                sum([c[2] for c in content]) / len(content),
            ]
        )
        / 3.0
    )

    return has_equal_alphas and content_avg <= 0.5


@transaction.atomic
def update(user_data: Dict) -> bool:
    user_slack_profile = user_data.get("profile")
    user_slack_email = user_slack_profile.get("email")
    user = User.objects.filter(email=user_slack_email).first()
    profile_picture_updated = False
    if user:
        user.slack_id = user_data.get("id")
        user.slack_status_text = user_slack_profile.get("status_text")
        user.slack_status_emoji = user_slack_profile.get("status_emoji")
        user.slack_display_name = user_slack_profile.get("display_name")

        user_slack_image_original = user_slack_profile.get("image_original")

        # Update the profile picture only if it changed
        if user.updated_at < timezone.now() - timezone.timedelta(seconds=10):
            response = requests.get(user_slack_image_original)
            if response.status_code == 200:
                profile_picture_file = BytesIO(response.content)
                # If it differs with the Slack picture we have saved
                # Need to build it again on ByesIO as it will be read later
                if not same_image(
                    file_1=BytesIO(response.content), file_2=user.slack_picture
                ):
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

        user.save()

        # TODO: Don't create a update look, needs to be checked
        # Yes, this will keep the worker completely stuck here, no other solution
        # for now due to Slack sending a ton of events too close to each other
        # time.sleep(2)
        #
        # if profile_picture_updated and user.slack_token:
        #     picture_success, picture_hash = set_picture(
        #         token=user.slack_token, file=BytesIO(user.slack_picture.file.read())
        #     )
        #     return picture_success
        return True
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


def warn_registration(id: UUID):
    user_obj = User.objects.get(id=id)
    if user_obj and user_obj.slack_id:
        user_finish_before = timezone.localtime(
            timezone.now() + timezone.timedelta(days=WARNING_TIME_DAYS)
        )

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nWe noticed you haven't finished registering :rotating_light: on our site. In order for us to be able to offer you the most out of this workplace *we need you to complete your details*, it will take only a minute :clock1:. If you don't manage to do so by {user_finish_before.strftime('%A %-d, %B %Y')} we will have to deactivate your account :grimacing:.",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": ":white_check_mark: Finish my registration",
                        },
                        "style": "primary",
                        "url": f"{APP_FULL_DOMAIN}{reverse('user_login')}",
                    }
                ],
            },
        ]

        response = messaging.api.slack.channel.send_message(
            external_id=user_obj.slack_id,
            blocks=blocks,
            unfurl_links=False,
            unfurl_media=False,
        )

        log.create(type=LogType.WARNING, target=user_obj, data=response.data)
