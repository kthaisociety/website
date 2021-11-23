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
        # TODO Should a message be sent?
        return

    user = User.objects.filter(slack_id=user_id).first()
    if not user:
        # User hasn't linked their slack account with their kthais account
        # TODO Should a message be sent?
        block = [
            {
                "type": "section",
                "text": {
                    "type": "markdown",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nYou have tried to register to the event{( ' '+event.name if event.name else '' )}, but your slack account is not connected with your KTHAIS' account. After connecting your account, you should finish the registration to this event on the webpage.",
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
                        "url": f"{APP_FULL_DOMAIN}{reverse('user_dashboard')}",
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
        # TODO Should a message be sent?
        block = [
            {
                "type": "section",
                "text": {
                    "type": "markdown",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nWe know that you really want to attend to {( event.name if event.name else 'this event' )}, but you are already registered.",
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

    if not event.registration_available or not event.is_signup_open:
        # Cannot register now
        # TODO Should a message be sent?
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
        # TODO Should a message be sent? Cannot collect resume from actions
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
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\nThe event { event.name+' ' if event.name else '' } will provide food and that's why we need to know if you have any restrictions. If you leave this section empty, we understand you don't have any.",
                },
            },
            {
                "type": "actions",
                "block_id": "diet",
                "elements": [
                    {
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
                    "type": "plain_text_input",
                    "initial_value": other_restriction,
                    "action_id": "other-restrictions",
                    "dispatch_action_config": {
                        "trigger_actions_on": ["on_character_entered"]
                    },
                },
                "label": {"type": "plain_text", "text": "OTHER", "emoji": true},
            },
            {
                "type": "actions",
                "block_id": "submit",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Send restrictions",
                            "emoji": true,
                        },
                        "value": "send",
                        "action_id": "send-food-restrictions",
                    }
                ],
            },
        ]
        """
        block = [
            {
                "type": "section",
                "text": {
                    "type": "markdown",
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nThe event { event.name+' ' if event.name else '' } has food and you have never specified.",
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
        """
        response = channel.send_message(
            external_id=user_id,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        InteractiveMessage.objects.create(
            slack_ts=response.message.ts, event=event_ts, diet="", diet_other=""
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
        # TODO Should a message be sent?
        send_registration_email(registration_id=registration.id)


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
                    "text": f"Hey there{(' ' + user_obj.name if user_obj.name else '')}!\n\nYou have tried to unregister to the event{( ' '+event.name if event.name else '' )}, but your slack account is not connected with your KTHAIS' account. You should unregister to this event on the webpage.",
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
        # TODO Should a message be sent?
        return

    registration.status = RegistrationStatus.CANCELLED
    registration.save()

    if registration:
        # TODO Should a message be sent?
        send_registration_email(registration_id=registration.id)


def action_handler(payload):
    msg = InteractiveMessage.objects.filter(slack_ts=payload.message.ts).first()
    if payload.actions.block_id == "diet":
        diet = ""
        for option in payload.actions[0].selected_options:
            diet += option[0].value + ","
        diet = diet[:-1]
        msg.diet = diet
        msg.save()
    elif payload.actions.block_id == "diet_other":
        msg.diet_other = payload.actions[
            0
        ].value  # This could be incorrect, it isn't said in the documentation
        msg.save()
        return
    elif payload.actions.block_id == "submit":
        event = Event.objects.published().filter(slack_ts=msg.event).first()
        user = User.objects.filter(slack_id=payload.user.id).first()
        diet = user.diet if msg.diet == "" else msg.diet
        diet_other = (
            msg.diet_other
            if len(msg.diet_other) > 0 and DietType.OTHER in msg.diet
            else user.diet_other
        )
        registration = Registration.objects.create(
            event=event,
            user=user,
            status=RegistrationStatus.REGISTERED,
            diet=diet,
            diet_other=diet_other,
        )

        blocks = []
        if registration:
            send_registration_email(registration_id=registration.id)
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":white_check_mark: You have registered properly. You can check the <{APP_FULL_DOMAIN}events/event/{ event.id }|event page>",
                    },
                }
            ]
        else:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":x: Something went wrong. You can ping us at <mailto:{ app_email_contact }|{ app_email_contact }> or check the <{APP_FULL_DOMAIN}events/event/{ event.id }|event page>",
                    },
                }
            ]

        channel.update_message(
            external_id=user_id,
            message_ts=msg.slack_ts,
            blocks=block,
            unfurl_links=False,
            unfurl_media=False,
        )
        # TODO Should we delete the object in InteractiveMessage.objects ?
