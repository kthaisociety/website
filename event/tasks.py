from uuid import UUID

from django.template.loader import render_to_string

from app.enums import MailTag
from app.utils import get_notification_template, get_substitutions_templates, send_email
from event.enums import RegistrationStatus
from event.models import Registration


# @shared_task
def send_registration_email(registration_id: UUID):
    context = get_substitutions_templates()
    registration = Registration.objects.get(id=registration_id)
    context["registration"] = registration
    context["user"] = registration.user

    if registration.status in [
        RegistrationStatus.REQUESTED,
        RegistrationStatus.REGISTERED,
    ]:
        task = "register"
    elif registration.status == RegistrationStatus.CANCELLED:
        task = "cancel"
    else:
        task = None

    if task:
        template = get_notification_template(
            method="email", app="event", task=task, format="html"
        )
        subject = get_notification_template(
            method="email", app="event", task=task, format="subject"
        )
        body = render_to_string(template, context)

        subject = subject.format(event=registration.event.name)

        send_email(
            subject=subject, body=body, to=registration.user.email, tags=[MailTag.EVENT]
        )


# @shared_task
def send_url_email(registration_id: UUID):
    context = get_substitutions_templates()
    registration = Registration.objects.get(id=registration_id)
    context["registration"] = registration
    context["user"] = registration.user

    if registration.status in [
        RegistrationStatus.REGISTERED,
        RegistrationStatus.JOINED,
        RegistrationStatus.ATTENDED,
    ]:
        template = get_notification_template(
            method="email", app="event", task="url", format="html"
        )
        subject = get_notification_template(
            method="email", app="event", task="url", format="subject"
        )
        body = render_to_string(template, context)

        subject = subject.format(event=registration.event.name)

        send_email(
            subject=subject, body=body, to=registration.user.email, tags=[MailTag.EVENT]
        )
