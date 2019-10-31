import re

from django.conf import settings
from app.variables import APP_ORGANISER_EMAIL_REGEX


def get_substitutions_templates():
    return {
        "app_name": getattr(settings, "APP_NAME", None),
        "app_description": getattr(settings, "APP_DESCRIPTION", None),
        "app_timezone": getattr(settings, "APP_TIMEZONE", None),
        "app_domain": getattr(settings, "APP_DOMAIN", None),
        "app_email_contact": getattr(settings, "APP_EMAIL_CONTACT", None),
        "app_email_webdev": getattr(settings, "APP_EMAIL_WEBDEV", None),
        "app_sn_facebook": getattr(settings, "APP_SN_FACEBOOK", None),
        "app_sn_instagram": getattr(settings, "APP_SN_INSTAGRAM", None),
        "app_sn_linkedin": getattr(settings, "APP_SN_LINKEDIN", None),
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
    }


def is_email_organiser(email):
    return re.match(APP_ORGANISER_EMAIL_REGEX, email)
