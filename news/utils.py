from typing import List

from django.db.models import Q
from django.utils import timezone

from news.models import Article, Pin


def get_latest_articles() -> List[Article]:
    return Article.objects.published().order_by("-created_at")[:5]


def get_latest_pin() -> Pin:
    return (
        Pin.objects.filter(
            Q(date_from__isnull=True) | Q(date_from__lte=timezone.now()),
            Q(date_to__isnull=True) | Q(date_to__gte=timezone.now()),
        )
        .order_by("-created_at")
        .first()
    )
