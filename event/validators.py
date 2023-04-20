import re

from django.core.exceptions import ValidationError


def validate_location(value):
    if not re.match(r"^(.+, )?.+, .+, .+$", value):
        raise ValidationError(
            "The location venue, city and country are mandatory",
        )
