import re
from typing import Dict, List, Optional, Tuple

import requests
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

# Make sure this variable is defined correctly somewhere in your settings or as a constant in your script:
APP_BLOG_MEDIUM = 'medium.com/kth-ai-society'

from news.enums import ArticleStatus, ArticleType
from news.models import Article, Author
from user.enums import UserType
from user.models import User

def get_medium_articles() -> Optional[List[Dict]]:
    # Construct the RSS URL correctly
    rss_url = f"https://{APP_BLOG_MEDIUM}/feed"
    response = requests.get(f"https://api.rss2json.com/v1/api.json?rss_url={rss_url}")

    if response.status_code != 200:
        return None

    content = response.json()
    if content.get("status", "error") != "ok":
        return None

    articles = []
    for item in content.get("items", []):
        body = item.get("content", "").strip()
        # Simplify the processing by directly using strip() to clean strings
        articles.append({
            "title": item.get("title", "").strip(),
            "author": item.get("author", "").strip(),
            "external_url": item.get("guid"),
            "image": item.get("thumbnail"),
            "body": body,
        })

    return articles

@transaction.atomic
def import_medium_articles() -> Tuple[bool, int, int]:
    medium_articles = get_medium_articles()

    if not medium_articles:
        return False, 0, 0

    existing_articles = {
        article.external_url: article
        for article in Article.objects.filter(type=ArticleType.MEDIUM)
    }

    possible_authors = User.objects.filter(Q(is_author=True) | Q(type=UserType.ORGANISER)).all()

    new_articles = []
    updated_articles = []
    new_authors = []
    article_images = {}

    for medium_article in medium_articles:
        slug = f"{slugify(medium_article['title'])}-{int(timezone.now().timestamp())}"
        response = requests.get(medium_article["image"])
        if response.status_code == 200:
            article_images[medium_article["external_url"]] = ContentFile(response.content)

        if medium_article["external_url"] in existing_articles:
            article = existing_articles[medium_article["external_url"]]
            article.title = medium_article["title"]
            article.body = medium_article["body"]
            updated_articles.append(article)
        else:
            article = Article(
                title=medium_article["title"],
                slug=slug,
                body=medium_article["body"],
                external_url=medium_article["external_url"],
                type=ArticleType.MEDIUM,
                status=ArticleStatus.PUBLISHED,
            )
            new_articles.append(article)

            body_lower = medium_article["body"].lower()
            for possible_author in possible_authors:
                if possible_author.full_name.lower() in body_lower:
                    new_authors.append(Author(article=article, user=possible_author))

    Article.objects.bulk_create(new_articles)
    Author.objects.bulk_create(new_authors)
    Article.objects.bulk_update(updated_articles, fields=["title", "body"])

    for article in new_articles + updated_articles:
        if article.external_url in article_images:
            article.picture.save(f"{article.slug}.jpg", article_images[article.external_url], save=True)

    return True, len(new_articles), len(updated_articles)
