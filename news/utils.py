from typing import List

from news.models import Article, Pin


def get_latest_articles() -> List[Article]:
    return Article.objects.published().order_by("-created_at")[:5]


def get_latest_pin() -> Pin:
    return Pin.objects.order_by("-created_at").first()
