from uuid import UUID

from django.template.loader import render_to_string

from app.enums import MailTag
from app.utils import get_notification_template, get_substitutions_templates, send_email
from user.models import User


# @shared_task
def send_verify_email(user_id: UUID):
    context = get_substitutions_templates()
    user = User.objects.get(id=user_id)
    context["user"] = user
    template = get_notification_template(
        method="email", app="user", task="register", format="html"
    )
    subject = get_notification_template(
        method="email", app="user", task="register", format="subject"
    )
    body = render_to_string(template, context)

    send_email(subject=subject, body=body, to=user.email, tags=[MailTag.REGISTER])


# @shared_task
def send_password_email(user_id: UUID):
    context = get_substitutions_templates()
    user = User.objects.get(id=user_id)
    context["user"] = user
    template = get_notification_template(
        method="email", app="user", task="password", format="html"
    )
    subject = get_notification_template(
        method="email", app="user", task="password", format="subject"
    )
    body = render_to_string(template, context)

    send_email(subject=subject, body=body, to=user.email, tags=[MailTag.PASSWORD])


# @shared_task
def send_imported_email(user_id: UUID):
    context = get_substitutions_templates()
    user = User.objects.get(id=user_id)
    context["user"] = user
    template = get_notification_template(
        method="email", app="user", task="imported", format="html"
    )
    subject = get_notification_template(
        method="email", app="user", task="imported", format="subject"
    )
    body = render_to_string(template, context)

    send_email(subject=subject, body=body, to=user.email, tags=[MailTag.PASSWORD])


# @shared_task
def send_slack_email(user_id: UUID):
    context = get_substitutions_templates()
    user = User.objects.get(id=user_id)
    context["user"] = user
    template = get_notification_template(
        method="email", app="user", task="slack", format="html"
    )
    subject = get_notification_template(
        method="email", app="user", task="slack", format="subject"
    )
    body = render_to_string(template, context)

    send_email(subject=subject, body=body, to=user.email, tags=[MailTag.SLACK])


# @shared_task
def send_created_email(user_id: UUID):
    context = get_substitutions_templates()
    user = User.objects.get(id=user_id)
    context["user"] = user
    template = get_notification_template(
        method="email", app="user", task="created", format="html"
    )
    subject = get_notification_template(
        method="email", app="user", task="created", format="subject"
    )
    body = render_to_string(template, context)

    send_email(subject=subject, body=body, to=user.email, tags=[MailTag.CREATED])
