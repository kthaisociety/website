import base64
import math
import os

from django import template
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from django_markup.markup import formatter

from app import settings
from app.settings import STATICFILES_DIRS, STATIC_URL, DEBUG, APP_DOMAIN
from app.variables import APP_LOCALHOST
from event.enums import AttachmentType

register = template.Library()


@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")


@register.filter
def apply_markup(text, filter_name):
    return mark_safe(formatter(text, filter_name))


@register.filter
def extract_app(url):
    return [u for u in url.split("/") if u][0]


@register.filter
def extract_slug(url):
    return url.split("/")[-1]


@register.filter
def year_from_now(years):
    return timezone.now().year + years


@register.simple_tag
def image_as_base64(image_path):
    try:
        image_full_path = os.path.join(STATICFILES_DIRS[0], image_path)
    except FileNotFoundError:
        return None
    with open(image_full_path, "rb") as img_f:
        encoded_string = base64.b64encode(img_f.read())
    return "data:image/%s;base64,%s" % (
        image_path.split(".")[-1],
        encoded_string.decode("utf-8"),
    )


@register.simple_tag
def full_url(name, *args):
    return f"https://{APP_DOMAIN}{reverse(name, args=args)}"


@register.simple_tag
def full_static(path):
    # Retrieve assets from production on beta domain
    app_domain_prod = APP_DOMAIN
    if DEBUG and APP_DOMAIN != APP_LOCALHOST and app_domain_prod.count(".") > 1:
        app_domain_prod = "https://" + ".".join(app_domain_prod.split(".")[1:])
    else:
        app_domain_prod = "https://" + app_domain_prod
    return f"{app_domain_prod}{STATIC_URL}{path}"


@register.filter
def event_attachment_type(value):
    return AttachmentType(value)


@register.filter
def timedelta_display(time: timezone.timedelta):
    seconds = time.total_seconds()
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "{:02d}:{:02d}:{:02d}".format(math.floor(h), math.floor(m), math.floor(s))


@register.filter
def time_left(time: timezone.datetime):
    return time - timezone.now()


@register.filter
def days_left(timedelta: timezone.timedelta):
    return int(timedelta.total_seconds() // (60 * 60 * 24))
