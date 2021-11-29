from django.urls import reverse

from user.models import User
from event.models import Event, Registration
from event.enums import RegistrationStatus
from user.enums import DietType, DietTypeDict
from app.settings import APP_FULL_DOMAIN

from messaging.api.slack import channel


def join_event(user_id: str, event_ts: str):
    event = Event.objects.published().filter(slack_ts=event_ts).first()
    if not event:
        # User has reacted to a message with the emoji, but it is not an event
        # announcement
        return

    user = User.objects.filter(slack_id=user_id).first()
    if not user:
        # User hasn't linked their slack account with their kthais account
        block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nYou have tried to register to the event{( ' '+event.name if event.name else '' )}, but your slack account is not connected with your KTHAIS' account or you don't have one. Please, you should finish the registration to this event on the webpage.",
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
                            "text": ":white_check_mark: Connect your slack account on your dashboard.",
                        },
                        "style": "primary",
                        "url": f"{APP_FULL_DOMAIN}events/event/{ event.id }",
                    }
                ],
            },
        ]

        response = channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        return

    registration = Registration.objects.filter(event=event, user=user).first()
    if registration:
        # User has already registered to the event.
        block = [
            {
                "type": "section",
                "text": {
                    "type": "markdown",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nWe know that you really want to attend to {( event.name if event.name else 'this event' )}, but you are already registered. We are going to send you an email with more details.",
                },
            },
        ]

        response = channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        send_registration_email(registration_id=registration.id)
        return

    if not event.registration_available or not event.is_signup_open:
        # Cannot register now
        block = [
            {
                "type": "section",
                "text": {
                    "type": "markdown",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\n. Sorry, registration closed! Ping us at { app_email_contact } if you need help.",
                },
            },
        ]

        response = channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        return

    if event.collect_resume and not user.resume:
        # The event requires a resume and the user has not upload one in kthais.com
        block = [
            {
                "type": "section",
                "text": {
                    "type": "markdown",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nThe event { event.name+' ' if event.name else '' } requires a resume but you have never upload one.",
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
                            "text": ":white_check_mark: Register to event on webpage.",
                        },
                        "style": "primary",
                        "url": f"{APP_FULL_DOMAIN}events/event/{ event.id }",
                    }
                ],
            },
        ]

        response = channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        return

    if event.has_food:
        # The event has food and it will be collected
        # TODO
        registration = Registration.objects.create(
            event=event,
            user=user,
            status=RegistrationStatus.REGISTERED,
            diet=user.diet,
            diet_other=user.diet_other,
        )
        if not registration:
            block = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nSomething went wrong when you tried to register to {( ' '+event.name if event.name else '' )}. Please, ping us at { app_email_contact } and visit the page event to finish your registration.",
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
                                "text": ":white_check_mark: Connect your slack account on your dashboard.",
                            },
                            "style": "primary",
                            "url": f"{APP_FULL_DOMAIN}events/event/{ event.id }",
                        }
                    ],
                },
            ]

            response = channel.send_message(
                external_id=user_id,
                blocks=block,
                unfurl_links=False,
                unfurl_media=False,
            )

            return
        initial_options = [
            {"text": {"type": "mrkdwn", "text": DietTypeDict[int(t)]}, "value": t}
            for t in user.diet.split(",")
        ]
        other_restriction = user.diet_other
        diet_options = [
            {"text": {"type": "mrkdwn", "text": DietTypeDict[key]}, "value": str(key)}
            for key in DietTypeDict
        ]
        block = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Dietary restrictions"},
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\nNow, you are registered to the event{ ' '+event.name if event.name else '' }. This event will provide you with food, you can add your food restrictions from here.",
                },
            },
            {
                "type": "actions",
                "block_id": "diet",
                "elements": [
                    {
                        "action_id": registration.id,
                        "type": "checkboxes",
                        "initial_options": initial_options,
                        "options": diet_options,
                    }
                ],
            },
        ]
        if str(DietType.OTHER) in user.diet:
            block += [
                {
                    "type": "input",
                    "block_id": "diet_other",
                    "element": {
                        "action_id": registration.id,
                        "type": "plain_text_input",
                        "initial_value": other_restriction,
                        "action_id": "other-restrictions",
                        "dispatch_action_config": {
                            "trigger_actions_on": ["on_character_entered"]
                        },
                    },
                    "label": {"type": "plain_text", "text": "OTHER", "emoji": true},
                },
            ]
        response = channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        return

    registration = Registration.objects.create(
        event=event,
        user=user,
        status=RegistrationStatus.REGISTERED,
        diet=user.diet,
        diet_other=user.diet_other,
    )
    if registration:
        block = [
            {
                "type": "section",
                "text": {
                    "type": "markdown",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nYou have successfully registered to the event {( event.name if event.name else 'this event' )}. We are going to send you an email with more details.",
                },
            },
        ]

        response = channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        send_registration_email(registration_id=registration.id)
    else:
        block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nSomething went wrong when you tried to register to {( ' '+event.name if event.name else '' )}. Please, ping us at { app_email_contact } and visit the page event to finish your registration.",
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
                            "text": ":white_check_mark: Connect your slack account on your dashboard.",
                        },
                        "style": "primary",
                        "url": f"{APP_FULL_DOMAIN}events/event/{ event.id }",
                    }
                ],
            },
        ]

        response = channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )


def leave_event(user_id: str, event_ts: str):
    event = Event.objects.published().filter(slack_ts=event_ts).first()
    if not event:
        # User has reacted to a message with the emoji, but it is not an event
        # announcement
        return

    user = User.objects.filter(slack_id=user_id).first()
    if not user:
        # User hasn't linked their slack account with their kthais account
        block = [
            {
                "type": "section",
                "text": {
                    "type": "markdown",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nYou have tried to unregister to the event{( ' '+event.name if event.name else '' )}, but your slack account is not connected with your KTHAIS' account or you don't have one. Please, you should finish on the webpage.",
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
                            "text": ":white_check_mark: Go to event page.",
                        },
                        "style": "primary",
                        "url": f"{APP_FULL_DOMAIN}events/event/{ event.id }",
                    },
                ],
            },
        ]

        response = channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        return

    registration = Registration.objects.filter(event=event, user=user).first()
    if not registration:
        # User is not registered to the event.
        block = [
            {
                "type": "section",
                "text": {
                    "type": "markdown",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nYou are trying to unregister to {( event.name if event.name else 'this event' )}, but you are not registered. Check the event page.",
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
                            "text": ":white_check_mark: Go to event page.",
                        },
                        "style": "primary",
                        "url": f"{APP_FULL_DOMAIN}events/event/{ event.id }",
                    },
                ],
            },
        ]

        response = channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        return

    registration.status = RegistrationStatus.CANCELLED
    registration.save()

    if registration:
        block = [
            {
                "type": "section",
                "text": {
                    "type": "markdown",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nYou have successfully unregistered to the event {( event.name if event.name else 'this event' )}. We are going to send you an email with more details.",
                },
            },
        ]

        response = channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        send_registration_email(registration_id=registration.id)
    else:
        block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nSomething went wrong when you tried to unregister to {( ' '+event.name if event.name else '' )}. Please, ping us at { app_email_contact } and visit the page event to finish your registration.",
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
                            "text": ":white_check_mark: Connect your slack account on your dashboard.",
                        },
                        "style": "primary",
                        "url": f"{APP_FULL_DOMAIN}events/event/{ event.id }",
                    }
                ],
            },
        ]

        response = channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )


def action_handler(payload):
    registration = Registration.objects.filter(id=payload.actions[0].action_id).first()
    if payload.actions.block_id == "diet":
        diet = ""
        for option in payload.actions[0].selected_options:
            diet += option[0].value + ","
        has_other = str(DietType.OTHER) in diet
        diet = diet[:-1]

        registration.diet = diet
        registration.save()

        if has_other and not str(DietType.OTHER) in registration.diet:
            initial_options = [
                {"text": {"type": "mrkdwn", "text": DietTypeDict[int(t)]}, "value": t}
                for t in user.diet.split(",")
            ]
            other_restriction = user.diet_other
            diet_options = [
                {
                    "text": {"type": "mrkdwn", "text": DietTypeDict[key]},
                    "value": str(key),
                }
                for key in DietTypeDict
            ]
            block = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "Dietary restrictions"},
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\nNow, you are registered to the event{ ' '+event.name if event.name else '' }. This event will provide you with food, you can add your food restrictions from here.",
                    },
                },
                {
                    "type": "actions",
                    "block_id": "diet",
                    "elements": [
                        {
                            "action_id": registration.id,
                            "type": "checkboxes",
                            "initial_options": initial_options,
                            "options": diet_options,
                        }
                    ],
                },
                {
                    "type": "input",
                    "block_id": "diet_other",
                    "element": {
                        "action_id": registration.id,
                        "type": "plain_text_input",
                        "initial_value": other_restriction,
                        "action_id": "other-restrictions",
                        "dispatch_action_config": {
                            "trigger_actions_on": ["on_character_entered"]
                        },
                    },
                    "label": {"type": "plain_text", "text": "OTHER", "emoji": true},
                },
            ]
            channel.update_message(
                external_id=user_id,
                message_ts=payload.message.ts,
                blocks=block,
                unfurl_links=False,
                unfurl_media=False,
            )
        elif not has_other and str(DietType.OTHER) in registration.diet:
            initial_options = [
                {"text": {"type": "mrkdwn", "text": DietTypeDict[int(t)]}, "value": t}
                for t in user.diet.split(",")
            ]
            other_restriction = user.diet_other
            diet_options = [
                {
                    "text": {"type": "mrkdwn", "text": DietTypeDict[key]},
                    "value": str(key),
                }
                for key in DietTypeDict
            ]
            block = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "Dietary restrictions"},
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\nNow, you are registered to the event{ ' '+event.name if event.name else '' }. This event will provide you with food, you can add your food restrictions from here.",
                    },
                },
                {
                    "type": "actions",
                    "block_id": "diet",
                    "elements": [
                        {
                            "action_id": registration.id,
                            "type": "checkboxes",
                            "initial_options": initial_options,
                            "options": diet_options,
                        }
                    ],
                },
            ]
            channel.update_message(
                external_id=user_id,
                message_ts=payload.message.ts,
                blocks=block,
                unfurl_links=False,
                unfurl_media=False,
            )
    elif payload.actions.block_id == "diet_other":
        registration.diet_other = payload.actions[0].value
        registration.save()
        return
