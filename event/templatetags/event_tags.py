import pytz
from django import template
from django.utils import timezone

from event.consts import SCHEDULE_EMOJIS
from event.enums import ScheduleType

register = template.Library()

ctz = timezone.get_current_timezone()


@register.filter
def display_clock(time: timezone.datetime):
    time = time.astimezone(ctz)
    base = int("1F54F", 16)
    hour = time.hour % 12
    if hour == 0:
        hour = 12
    return chr(base + hour)


@register.filter
def one_year(time: timezone.datetime):
    return time.replace(year=time.year - 1)


@register.filter
def schedule_emoji(type: ScheduleType):
    return SCHEDULE_EMOJIS.get(type, "")
