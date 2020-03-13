from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe

from django_markup.markup import formatter

from app import settings

register = template.Library()


@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")


@register.filter
def apply_markup(text, filter_name):
    return mark_safe(formatter(text, filter_name))


@register.filter
def extract_app(url):
    return url.split("/")[0]


@register.filter
def extract_slug(url):
    return url.split("/")[-1]


@register.filter
def year_from_now(years):
    return timezone.now().year + years