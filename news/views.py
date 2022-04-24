from django.http import HttpResponseNotFound
from django.shortcuts import render

from news.models import Article


def article(request, year, month, day, slug):
    article_obj = (
        Article.objects.published()
        .filter(
            slug=slug,
            created_at__year=int(year),
            created_at__month=int(month),
            created_at__day=int(day),
        )
        .first()
    )
    if article_obj:
        return render(request, "article.html", {"article": article_obj})
    return HttpResponseNotFound()


def articles(request):
    article_objs = Article.objects.published().order_by("-created_at")
    return render(request, "articles.html", {"articles": article_objs})
