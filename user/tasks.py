from celery import shared_task
from django.template.loader import render_to_string

from app.enums import MailTag
from app.utils import get_notification_template, send_email, get_substitutions_templates
from user.models import User


@shared_task
def send_verify_email(user: User):
    context = get_substitutions_templates()
    context["user"] = user
    template = get_notification_template(
        method="email", app="user", task="register", format="html"
    )
    subject = get_notification_template(
        method="email", app="user", task="register", format="subject"
    )
    body = render_to_string(template, context)

    send_email(subject=subject, body=body, to=user.email, tags=[MailTag.REGISTER])
