from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def display_clock(time):
    base = int("1F54F", 16)
    hour = time.hour % 12
    if hour == 0:
        hour = 12
    return chr(base + hour)


@register.filter
def one_year(time: timezone.datetime):
    return time.replace(year=time.year - 1)
