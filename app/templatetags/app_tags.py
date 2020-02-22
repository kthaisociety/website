from django import template
from markdownx.utils import markdownify

from app import settings

register = template.Library()


@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")


@register.filter
def markdown_to_html(text):
    return markdownify(text)


@register.filter
def extract_app(url):
    return url.split("/")[0]


@register.filter
def extract_slug(url):
    return url.split("/")[-1]

