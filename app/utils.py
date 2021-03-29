import re
from typing import Optional

import html2text
from django.conf import settings
from django.contrib import admin
from django.core.mail import EmailMultiAlternatives

from app.consts import UNIVERSITIES, PROGRAMMES
from app.variables import (
    APP_ORGANISER_EMAIL_REGEX,
    APP_NAME,
    APP_EMAIL_NOREPLY,
    APP_EMAIL_CONTACT,
)


def get_substitutions_templates(request: Optional = None):
    maintenance_mode = getattr(settings, "MAINTENANCE_MODE", False)
    if request and not (request.user.is_authenticated and request.user.is_organiser):
        maintenance_mode = False
    return {
        "app_name": getattr(settings, "APP_NAME", None),
        "app_description": getattr(settings, "APP_DESCRIPTION", None),
        "app_timezone": getattr(settings, "APP_TIMEZONE", None),
        "app_domain": getattr(settings, "APP_DOMAIN", None),
        "app_protocol": getattr(settings, "APP_PROTOCOL", None),
        "app_full_domain": getattr(settings, "APP_FULL_DOMAIN", None),
        "app_email_contact": getattr(settings, "APP_EMAIL_CONTACT", None),
        "app_email_webdev": getattr(settings, "APP_EMAIL_WEBDEV", None),
        "app_sn_facebook": getattr(settings, "APP_SN_FACEBOOK", None),
        "app_sn_twitter": getattr(settings, "APP_SN_TWITTER", None),
        "app_sn_instagram": getattr(settings, "APP_SN_INSTAGRAM", None),
        "app_sn_youtube": getattr(settings, "APP_SN_YOUTUBE", None),
        "app_sn_linkedin": getattr(settings, "APP_SN_LINKEDIN", None),
        "app_sn_medium": getattr(settings, "APP_SN_MEDIUM", None),
        "app_sn_github": getattr(settings, "APP_SN_GITHUB", None),
        "app_legal_name": getattr(settings, "APP_LEGAL_NAME", None),
        "app_legal_organisation_name": getattr(
            settings, "APP_LEGAL_ORGANISATION_NAME", None
        ),
        "app_legal_organisation_number": getattr(
            settings, "APP_LEGAL_ORGANISATION_NUMBER", None
        ),
        "app_legal_organisation_bankgiro": getattr(
            settings, "APP_LEGAL_ORGANISATION_BANKGIRO", None
        ),
        "app_legal_address_1": getattr(settings, "APP_LEGAL_ADDRESS_1", None),
        "app_legal_address_2": getattr(settings, "APP_LEGAL_ADDRESS_2", None),
        "app_legal_postcode": getattr(settings, "APP_LEGAL_POSTCODE", None),
        "app_legal_city": getattr(settings, "APP_LEGAL_CITY", None),
        "app_legal_country": getattr(settings, "APP_LEGAL_COUNTRY", None),
        "pre_calendar_url": "webcal://"
        + getattr(settings, "APP_DOMAIN", "")
        .replace("https://", "")
        .replace("http://", ""),
        "maintenance_mode": maintenance_mode,
        "const_universities": UNIVERSITIES,
        "const_programmes": PROGRAMMES,
        "sl_id": getattr(settings, "SL_ID", None),
        "sl_user_scopes": getattr(settings, "SL_USER_SCOPES", None),
    }


def is_email_organiser(email):
    return re.match(APP_ORGANISER_EMAIL_REGEX, email)


def get_notification_template(method: str, app: str, task: str, format: str):
    return settings.NOTIFY_TEMPLATES[method][app][task][format]


def send_email(
    subject,
    body,
    to,
    from_email=None,
    reply_to=None,
    tags=None,
    track_clicks=False,
    fail_silently=False,
    attachments=None,
):
    if tags is None:
        tags = []

    tags += APP_NAME.lower()

    if to and not isinstance(to, (list, tuple)):
        to = [to]

    if reply_to and not isinstance(reply_to, (list, tuple)):
        reply_to = [reply_to]

    body_plain = html2text.html2text(body)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_plain,
        from_email=from_email or APP_NAME + "<" + APP_EMAIL_NOREPLY + ">",
        to=to,
        reply_to=reply_to or [APP_NAME + "<" + APP_EMAIL_CONTACT + ">"],
        attachments=attachments,
    )

    msg.attach_alternative(body, "text/html")

    if tags:
        msg.tags = tags

    msg.track_clicks = track_clicks

    return msg.send(fail_silently=fail_silently)


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
