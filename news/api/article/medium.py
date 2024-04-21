import re
from typing import Dict, List, Optional, Tuple

import requests
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from app.variables import APP_BLOG_MEDIUM
from news.enums import ArticleStatus, ArticleType
from news.models import Article, Author
from user.enums import UserType
from user.models import User


def get_medium_articles() -> Optional[List[Dict]]:
    response = requests.get(
        f"https://api.rss2json.com/v1/api.json?rss_url=https://{APP_BLOG_MEDIUM}/feed"
    )

    if response.status_code != 200:
        return None

    content = response.json()

    if content.get("status", "error") != "ok":
        return None

    articles = []
    for article in content.get("items", []):
        # Special space character
        body = article.get("content").replace(" ", " ").strip()
        body = re.sub(r".*\n", "", body, 1).strip()
        articles.append(
            {
                "title": article.get("title").strip(),
                "author": article.get("author").strip(),
                "external_url": article.get("guid"),
                "image": article.get("thumbnail"),
                "body": body,
            }
        )

    return articles


@transaction.atomic
def import_medium_articles() -> Tuple[bool, int, int]:
    medium_articles = get_medium_articles()

    if not medium_articles:
        return False, 0, 0

    articles = {
        article.external_url: article
        for article in Article.objects.filter(type=ArticleType.MEDIUM)
    }

    possible_authors = list(
        User.objects.filter(Q(is_author=True) | Q(type=UserType.ORGANISER))
    )

    new_articles = []
    updated_articles = []
    new_authors = []
    article_images = {}
    for medium_article in medium_articles:
        slug = (
            f"{slugify(medium_article.get('title'))}-{int(timezone.now().timestamp())}"
        )
        article_images[medium_article.get("external_url")] = ContentFile(
            requests.get(medium_article.get("image")).content
        )

        body = medium_article.get("body")
        authors_search = re.search(r"<p>\s*Authors\s*(:)?\s*<\/p>", body)
        if authors_search:
            pos = authors_search.start()
            if pos:
                body = body[:pos].strip()
        else:
            authors_search = re.search(
                r"<h[1-6]>\s*Author(s)?\s*(:)?\s*<\/h[1-6]>", body
            )
            if authors_search:
                pos = authors_search.start()
                if pos:
                    body = body[:pos].strip()

        if medium_article.get("external_url") in articles.keys():
            article = articles[medium_article.get("external_url")]
            article.title = medium_article.get("title")
            article.body = body
            updated_articles.append(article)
        else:
            article = Article(
                title=medium_article.get("title"),
                slug=slug,
                body=body,
                external_url=medium_article.get("external_url"),
                type=ArticleType.MEDIUM,
                status=ArticleStatus.PUBLISHED,
            )
            new_articles.append(article)

            body_lower = medium_article.get("body").lower()
            for possible_author in possible_authors:
                if possible_author.full_name.lower() in body_lower:
                    new_authors.append(Author(article=article, user=possible_author))

    articles = Article.objects.bulk_create(new_articles)
    Author.objects.bulk_create(new_authors)
    Article.objects.bulk_update(updated_articles, fields=("title", "body"))

    for article in list(articles) + updated_articles:
        if article.external_url in article_images:
            article.picture.save(
                f"{article.slug}.jpg", article_images[article.external_url], save=True
            )

    return True, len(new_articles), len(updated_articles)
