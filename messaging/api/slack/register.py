import re

from django.urls import reverse

from event.tasks import send_registration_email
from user.models import User
from event.models import Event, Registration
from event.enums import RegistrationStatus, SignupStatus
from user.enums import DietType, DietTypeDict
from app.settings import APP_FULL_DOMAIN, SL_JOIN_EVENT

from messaging.api.slack import channel


def join_event(user_id: str, event_ts: str) -> bool:
    event_obj = (
        Event.objects.published()
        .filter(slack_ts=event_ts, signup_url__isnull=True)
        .first()
    )

    if not event_obj:
        # User has reacted to a message with the emoji but it is not an event announcement
        return False

    user_obj = User.objects.filter(slack_id=user_id).first()

    salutation = "Hey there :wave:!"
    if user_obj:
        salutation = f"Hey there {user_obj.name} :wave:!"

    if user_obj:
        registration_obj = Registration.objects.filter(
            event=event_obj, user=user_obj
        ).first()
        if registration_obj:
            # User has already registered to the event
            if registration_obj.is_active:
                block = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{salutation}\n\nWe know that you really want to attend *{event_obj.name}* but you are already registered! Make sure to check your email inbox :incoming_envelope:, we have sent you the registration email again :blush:.",
                        },
                    },
                ]
            else:
                block = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{salutation}\n\nWe know that you really want to attend *{event_obj.name}* but you cancelled your registration! If you need assistance please let us know here on Slack :slack: and we'll be glad to help you out.",
                        },
                    },
                ]

            channel.send_message(
                external_id=user_id,
                blocks=block,
                unfurl_links=False,
                unfurl_media=False,
            )
            send_registration_email(registration_id=registration_obj.id)
            return True

    if not event_obj.is_signup_open:
        message = "Sorry, registration closed!"
        if event_obj.signup_status == SignupStatus.PAST:
            message = "Sorry, the event has already taken place!"
        elif event_obj.signup_status == SignupStatus.FULL:
            message = (
                "Sorry, the event is full as we have reached the attendance limit!"
            )
        elif event_obj.signup_status == SignupStatus.FUTURE:
            message = (
                "Sorry, the signup hasn't open yet. Make sure to check again soon!"
            )

        # Cannot register right now
        block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{salutation}\n\n{message}",
                },
            },
        ]

        channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        return False

    if not user_obj:
        # User hasn't linked their Slack account with their KTHAIS account
        block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{salutation}\n\nYou have tried to register to *{event_obj.name}* but your Slack account :slack: is not connected with your KTHAIS account :kthais:. Please, finish the registration :pencil: to this event on the webpage.",
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
                            "text": ":pencil: Register on the website",
                        },
                        "style": "primary",
                        "url": f"{APP_FULL_DOMAIN}{event_obj.url}",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": ":robot_face: Connect my account",
                        },
                        "url": f"{APP_FULL_DOMAIN}{reverse('user_login')}",
                    },
                ],
            },
        ]

        channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        return False

    if event_obj.collect_resume and not user_obj.resume:
        # The event requires a resume and the user has not uploaded one in the website
        block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{salutation}\n\nThe event *{event_obj.name}* requires a resumé :page_facing_up: but you have never uploaded one!",
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
                            "text": ":pencil: Register on the website",
                        },
                        "style": "primary",
                        "url": f"{APP_FULL_DOMAIN}{event_obj.url}",
                    },
                ],
            },
        ]

        channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        return False

    registration_obj = Registration.objects.create(
        event=event_obj,
        user=user_obj,
        status=RegistrationStatus.REGISTERED,
        diet=user_obj.diet,
        diet_other=user_obj.diet_other,
    )

    if event_obj.has_food:
        # The event has food and it will be collected
        user_diet = user_obj.diet or ""
        other_restriction = user_obj.diet_other or ""

        diet_checkboxes = {
            "action_id": f"event-registration-diet-{registration_obj.id}",
            "type": "checkboxes",
            "options": [
                {
                    "text": {"type": "mrkdwn", "text": DietTypeDict[diet]},
                    "value": str(diet.value),
                }
                for diet in DietType
                if diet != DietType.OTHER
            ],
        }

        if user_diet:
            diet_checkboxes["initial_options"] = [
                {
                    "text": {"type": "mrkdwn", "text": DietTypeDict[int(diet)]},
                    "value": diet,
                }
                for diet in user_diet.split(",")
                if int(diet) != DietType.OTHER
            ]

        block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{salutation}!\n\nYou are now registered to *{event_obj.name}*! This event will provide free food :sandwich: and that's why we need to know if you have any restrictions :dizzy_face:.",
                },
            },
            {
                "type": "actions",
                "block_id": "diet",
                "elements": [diet_checkboxes],
            },
            # {
            #     "type": "input",
            #     "block_id": "diet_other",
            #     "element": {
            #         "action_id": f"event-registration-diet-{registration_obj.id}",
            #         "type": "plain_text_input",
            #         "initial_value": other_restriction,
            #         "dispatch_action_config": {
            #             "trigger_actions_on": ["on_character_entered"]
            #         },
            #     },
            #     "label": {
            #         "type": "plain_text",
            #         "text": "Other restrictions",
            #         "emoji": True,
            #     },
            # },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": ":heavy_plus_sign: Other restrictions",
                        },
                        "style": "primary",
                        "url": f"{APP_FULL_DOMAIN}{event_obj.url}",
                    },
                ],
            },
        ]
        channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        return True

    block = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{salutation}!\n\nYou are now registered for *{event_obj.name}*! You should have received an email :incoming_envelope: with your registration confirmation, you will be notified closer to the event :date: with extra details if that is required. If you want to cancel your registration you just need to remove the reaction :{SL_JOIN_EVENT}:.",
            },
        },
    ]

    channel.send_message(
        external_id=user_id,
        blocks=block,
        unfurl_links=False,
        unfurl_media=False,
    )
    return True


def leave_event(user_id: str, event_ts: str) -> bool:
    event_obj = Event.objects.published().filter(slack_ts=event_ts).first()

    if not event_obj:
        # User has reacted to a message with the emoji, but it is not an event announcement
        return False

    user_obj = User.objects.filter(slack_id=user_id).first()

    salutation = "Hey there :wave:!"
    if user_obj:
        salutation = f"Hey there {user_obj.name} :wave:!"

    if not user_obj:
        # User hasn't linked their Slack account with their KTHAIS account
        block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{salutation}\n\nYou have tried to unregister for *{event_obj.name}* but your Slack account :slack: is not connected with your KTHAIS account :kthais:. Please, finish the cancellation :pencil: to this event on the webpage.",
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
                            "text": ":pencil: Cancel on the website",
                        },
                        "style": "primary",
                        "url": f"{APP_FULL_DOMAIN}{event_obj.url}",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": ":robot_face: Connect my account",
                        },
                        "url": f"{APP_FULL_DOMAIN}{reverse('user_login')}",
                    },
                ],
            },
        ]

        channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        return False

    registration_obj = Registration.objects.filter(
        event=event_obj, user=user_obj
    ).first()

    if not registration_obj:
        # User is not registered to the event
        return False

    if event_obj.signup_status == SignupStatus.PAST:
        # The event has already past
        block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{salutation}!\n\nThe event *{event_obj.name}* has already happened :date: and therefore we can't cancel your registration!",
                },
            },
        ]

        channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        return False

    registration_obj.status = RegistrationStatus.CANCELLED
    registration_obj.save()

    block = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{salutation}!\n\nYou are now unregistered for *{event_obj.name}*, we hope to see you in future events!",
            },
        },
    ]

    channel.send_message(
        external_id=user_id,
        blocks=block,
        unfurl_links=False,
        unfurl_media=False,
    )
    return True


def action_handler(payload):
    for action in payload["actions"]:
        action_id = action["action_id"]
        block_id = action["block_id"]
        if action_id.startswith("event-registration-diet"):
            try:
                _, registration_id = re.search(
                    r"^(event-registration-diet)-(\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b)$",
                    action_id,
                ).groups()
                registration_obj = Registration.objects.filter(
                    id=registration_id
                ).first()
                user_obj = registration_obj.user

                if block_id == "diet":
                    diet = ""
                    for option in action["selected_options"]:
                        diet += option["value"] + ","
                    diet = diet[:-1]

                    registration_obj.diet = diet
                    registration_obj.save()

                    user_obj.diet = diet
                    user_obj.save()
                elif block_id == "diet_other":
                    diet_other = action["value"]

                    diet = registration_obj.diet or user_obj.diet
                    if diet_other:
                        if diet:
                            diet = f"{diet},{str(DietType.OTHER.value)}"
                        else:
                            diet = str(DietType.OTHER.OTHER.value)
                    elif diet:
                        diet = ",".join(
                            [
                                d
                                for d in diet.split(",")
                                if d != str(DietType.OTHER.value)
                            ]
                        )

                    registration_obj.diet = diet
                    registration_obj.diet_other = diet_other
                    registration_obj.save()

                    user_obj.diet = diet
                    user_obj.diet_other = diet_other
                    user_obj.save()
            except AttributeError:
                pass
