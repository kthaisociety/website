import re

from app.variables import APP_ORGANISER_EMAIL_REGEX


def is_email_organiser(email):
    return re.match(APP_ORGANISER_EMAIL_REGEX, email)