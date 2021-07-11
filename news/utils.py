from typing import List

from news.models import Article


def get_latest_articles() -> List[Article]:
    featured_article = get_featured_article()
    return (
        Article.objects.published()
        .exclude(id=featured_article.id)
        .order_by("-created_at")[:5]
    )


def get_featured_article() -> Article:
    return (
        Article.objects.published()
        .filter(is_featured=True)
        .order_by("-created_at")
        .first()
    )
