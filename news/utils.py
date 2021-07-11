from typing import List

from news.models import Article


def get_latest_articles() -> List[Article]:
    articles = Article.objects.published()

    featured_article = get_featured_article()
    if featured_article:
        articles.exclude(id=featured_article.id)

    return articles.order_by("-created_at")[:5]


def get_featured_article() -> Article:
    return (
        Article.objects.published()
        .filter(is_featured=True)
        .order_by("-created_at")
        .first()
    )
