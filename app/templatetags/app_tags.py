import base64
import os

from django import template
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from django_markup.markup import formatter

from app import settings
from app.settings import STATICFILES_DIRS, STATIC_URL
from app.variables import APP_DOMAIN

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
    return 'data:image/%s;base64,%s' % (image_path.split(".")[-1], encoded_string.decode("utf-8"))


@register.simple_tag
def full_url(name, *args):
    return f"//{APP_DOMAIN}{reverse(name, args=args)}"


@register.simple_tag
def full_static(path):
    return f"//{APP_DOMAIN}{STATIC_URL}{path}"
