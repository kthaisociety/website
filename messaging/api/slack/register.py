from django.urls import reverse

from event.tasks import send_registration_email
from user.models import User
from event.models import Event, Registration
from event.enums import RegistrationStatus, SignupStatus
from user.enums import DietType, DietTypeDict
from app.settings import APP_FULL_DOMAIN

from messaging.api.slack import channel


def join_event(user_id: str, event_ts: str) -> bool:
    event_obj = Event.objects.published().filter(slack_ts=event_ts).first()

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
                        "url": f"{APP_FULL_DOMAIN}events/event/{ event_obj.id }",
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
                        "url": f"{APP_FULL_DOMAIN}events/event/{ event_obj.id }",
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

    # if event_obj.has_food:
    #     # The event has food and it will be collected
    #     registration = Registration.objects.create(
    #         event=event,
    #         user=user,
    #         status=RegistrationStatus.REGISTERED,
    #         diet=user.diet,
    #         diet_other=user.diet_other,
    #     )
    #     if not registration:
    #         block = [
    #             {
    #                 "type": "section",
    #                 "text": {
    #                     "type": "mrkdwn",
    #                     "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nSomething went wrong when you tried to register to {( ' '+event.name if event.name else '' )}. Please, ping us at { app_email_contact } and visit the page event to finish your registration.",
    #                 },
    #             },
    #             {
    #                 "type": "actions",
    #                 "elements": [
    #                     {
    #                         "type": "button",
    #                         "text": {
    #                             "type": "plain_text",
    #                             "emoji": True,
    #                             "text": ":white_check_mark: Connect your slack account on your dashboard.",
    #                         },
    #                         "style": "primary",
    #                         "url": f"{APP_FULL_DOMAIN}events/event/{ event.id }",
    #                     }
    #                 ],
    #             },
    #         ]
    #
    #         response = channel.send_message(
    #             external_id=user_id,
    #             blocks=block,
    #             unfurl_links=False,
    #             unfurl_media=False,
    #         )
    #
    #         return
    #     initial_options = [
    #         {"text": {"type": "mrkdwn", "text": DietTypeDict[int(t)]}, "value": t}
    #         for t in user.diet.split(",")
    #     ]
    #     other_restriction = user.diet_other
    #     diet_options = [
    #         {"text": {"type": "mrkdwn", "text": DietTypeDict[key]}, "value": str(key)}
    #         for key in DietTypeDict
    #     ]
    #     block = [
    #         {
    #             "type": "header",
    #             "text": {"type": "plain_text", "text": "Dietary restrictions"},
    #         },
    #         {"type": "divider"},
    #         {
    #             "type": "section",
    #             "text": {
    #                 "type": "mrkdwn",
    #                 "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\nNow, you are registered to the event{ ' '+event.name if event.name else '' }. This event will provide you with food, you can add your food restrictions from here.",
    #             },
    #         },
    #         {
    #             "type": "actions",
    #             "block_id": "diet",
    #             "elements": [
    #                 {
    #                     "action_id": registration.id,
    #                     "type": "checkboxes",
    #                     "initial_options": initial_options,
    #                     "options": diet_options,
    #                 }
    #             ],
    #         },
    #     ]
    #     if str(DietType.OTHER) in user.diet:
    #         block += [
    #             {
    #                 "type": "input",
    #                 "block_id": "diet_other",
    #                 "element": {
    #                     "action_id": registration.id,
    #                     "type": "plain_text_input",
    #                     "initial_value": other_restriction,
    #                     "action_id": "other-restrictions",
    #                     "dispatch_action_config": {
    #                         "trigger_actions_on": ["on_character_entered"]
    #                     },
    #                 },
    #                 "label": {"type": "plain_text", "text": "OTHER", "emoji": true},
    #             },
    #         ]
    #     response = channel.send_message(
    #         external_id=user_id,
    #         blocks=block,
    #         unfurl_links=False,
    #         unfurl_media=False,
    #     )
    #     return

    Registration.objects.create(
        event=event_obj,
        user=user_obj,
        status=RegistrationStatus.REGISTERED,
        diet=user_obj.diet,
        diet_other=user_obj.diet_other,
    )

    block = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{salutation}!\n\nYou are now registered for *{event_obj.name}*! You should have received an email :incoming_envelope: with your registration confirmation, you will be notified closer to the event :date: with extra details if that is required.",
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
                        "url": f"{APP_FULL_DOMAIN}events/event/{ event_obj.id }",
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
        block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{salutation}!\n\nWe have tried to remove your registration to *{event_obj.name}* but we couldn't find it!",
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
                        "url": f"{APP_FULL_DOMAIN}events/event/{ event_obj.id }",
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
    registration = Registration.objects.filter(id=payload.actions[0].action_id).first()
    # if payload.actions.block_id == "diet":
    #     diet = ""
    #     for option in payload.actions[0].selected_options:
    #         diet += option[0].value + ","
    #     has_other = str(DietType.OTHER) in diet
    #     diet = diet[:-1]
    #
    #     registration.diet = diet
    #     registration.save()
    #
    #     if has_other and not str(DietType.OTHER) in registration.diet:
    #         initial_options = [
    #             {"text": {"type": "mrkdwn", "text": DietTypeDict[int(t)]}, "value": t}
    #             for t in user.diet.split(",")
    #         ]
    #         other_restriction = user.diet_other
    #         diet_options = [
    #             {
    #                 "text": {"type": "mrkdwn", "text": DietTypeDict[key]},
    #                 "value": str(key),
    #             }
    #             for key in DietTypeDict
    #         ]
    #         block = [
    #             {
    #                 "type": "header",
    #                 "text": {"type": "plain_text", "text": "Dietary restrictions"},
    #             },
    #             {"type": "divider"},
    #             {
    #                 "type": "section",
    #                 "text": {
    #                     "type": "mrkdwn",
    #                     "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\nNow, you are registered to the event{ ' '+event.name if event.name else '' }. This event will provide you with food, you can add your food restrictions from here.",
    #                 },
    #             },
    #             {
    #                 "type": "actions",
    #                 "block_id": "diet",
    #                 "elements": [
    #                     {
    #                         "action_id": registration.id,
    #                         "type": "checkboxes",
    #                         "initial_options": initial_options,
    #                         "options": diet_options,
    #                     }
    #                 ],
    #             },
    #             {
    #                 "type": "input",
    #                 "block_id": "diet_other",
    #                 "element": {
    #                     "action_id": registration.id,
    #                     "type": "plain_text_input",
    #                     "initial_value": other_restriction,
    #                     "action_id": "other-restrictions",
    #                     "dispatch_action_config": {
    #                         "trigger_actions_on": ["on_character_entered"]
    #                     },
    #                 },
    #                 "label": {"type": "plain_text", "text": "OTHER", "emoji": true},
    #             },
    #         ]
    #         channel.update_message(
    #             external_id=user_id,
    #             message_ts=payload.message.ts,
    #             blocks=block,
    #             unfurl_links=False,
    #             unfurl_media=False,
    #         )
    #     elif not has_other and str(DietType.OTHER) in registration.diet:
    #         initial_options = [
    #             {"text": {"type": "mrkdwn", "text": DietTypeDict[int(t)]}, "value": t}
    #             for t in user.diet.split(",")
    #         ]
    #         other_restriction = user.diet_other
    #         diet_options = [
    #             {
    #                 "text": {"type": "mrkdwn", "text": DietTypeDict[key]},
    #                 "value": str(key),
    #             }
    #             for key in DietTypeDict
    #         ]
    #         block = [
    #             {
    #                 "type": "header",
    #                 "text": {"type": "plain_text", "text": "Dietary restrictions"},
    #             },
    #             {"type": "divider"},
    #             {
    #                 "type": "section",
    #                 "text": {
    #                     "type": "mrkdwn",
    #                     "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\nNow, you are registered to the event{ ' '+event.name if event.name else '' }. This event will provide you with food, you can add your food restrictions from here.",
    #                 },
    #             },
    #             {
    #                 "type": "actions",
    #                 "block_id": "diet",
    #                 "elements": [
    #                     {
    #                         "action_id": registration.id,
    #                         "type": "checkboxes",
    #                         "initial_options": initial_options,
    #                         "options": diet_options,
    #                     }
    #                 ],
    #             },
    #         ]
    #         channel.update_message(
    #             external_id=user_id,
    #             message_ts=payload.message.ts,
    #             blocks=block,
    #             unfurl_links=False,
    #             unfurl_media=False,
    #         )
    # elif payload.actions.block_id == "diet_other":
    #     registration.diet_other = payload.actions[0].value
    #     registration.save()
    #     return
