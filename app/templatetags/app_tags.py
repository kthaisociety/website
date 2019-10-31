from django import template

from app import settings

register = template.Library()


@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")
