from uuid import UUID

import mailchimp_marketing
from mailchimp_marketing.api_client import ApiClientError

from app.settings import MAILCHIMP_KEY, MAILCHIMP_PREFIX, MAILCHIMP_LIST
from user.models import User


def update_newsletter_list(user_id: UUID):
    if not MAILCHIMP_KEY or not MAILCHIMP_PREFIX or not MAILCHIMP_LIST:
        return

    user = User.objects.get(id=user_id)
    if not user.registration_finished:
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
