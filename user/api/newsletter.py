import logging
from uuid import UUID

import mailchimp_marketing
from mailchimp_marketing.api_client import ApiClientError

from app.settings import MAILCHIMP_KEY, MAILCHIMP_LIST, MAILCHIMP_PREFIX
from user.models import User

_log = logging.getLogger(__name__)


def update_newsletter_list(user_id: UUID):
    if not MAILCHIMP_KEY or not MAILCHIMP_PREFIX or not MAILCHIMP_LIST:
        return

    user = User.objects.get(id=user_id)
    if not user.registration_finished or user.is_forgotten:
        return

    try:
        client = mailchimp_marketing.Client()
        client.set_config({"api_key": MAILCHIMP_KEY, "server": MAILCHIMP_PREFIX})
        client.lists.set_list_member(
            list_id=MAILCHIMP_LIST,
            subscriber_hash=user.subscriber_id,
            body={
                "email_address": user.email,
                "status_if_new": (
                    "subscribed" if user.is_subscriber else "unsubscribed"
                ),
                "email_type": "html",
                "merge_fields": {
                    "FNAME": user.name,
                    "LNAME": user.surname,
                    "LCITY": user.city,
                    "LCOUNTRY": user.country,
                    "LUNI": user.university,
                    "MMERGE3": user.degree,
                    "YEAR": user.graduation_year,
                },
                "tags": ["Member", "KTHAIS.com"],
            },
        )
    except ApiClientError:
        pass


def delete_user_newsletter(user_id: UUID):
    if not MAILCHIMP_KEY or not MAILCHIMP_PREFIX or not MAILCHIMP_LIST:
        return

    user = User.objects.get(id=user_id)
    try:
        client = mailchimp_marketing.Client()
        client.set_config({"api_key": MAILCHIMP_KEY, "server": MAILCHIMP_PREFIX})
        client.lists.delete_list_member_permanent(
            list_id=MAILCHIMP_LIST, subscriber_hash=user.subscriber_id
        )
    except ApiClientError as e:
        _log.error(e)
