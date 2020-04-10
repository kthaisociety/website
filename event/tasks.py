from uuid import UUID

from celery import shared_task
from django.template.loader import render_to_string

from app.enums import MailTag
from app.utils import get_notification_template, send_email, get_substitutions_templates
from event.enums import RegistrationStatus
from event.models import Registration


@shared_task
def send_registration_email(registration_id: UUID):
    context = get_substitutions_templates()
    registration = Registration.objects.get(id=registration_id)
    context["registration"] = registration

    if registration.status in [RegistrationStatus.REQUESTED, RegistrationStatus.REGISTERED]:
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

        send_email(subject=subject, body=body, to=registration.user.email, tags=[MailTag.EVENT])
