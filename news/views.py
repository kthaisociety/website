from django.http import HttpResponseNotFound
from django.shortcuts import render

from news.models import Article


def article(request, year, month, day, slug):
    article = (
        Article.objects.published()
        .filter(
            slug=slug,
            created_at__year=int(year),
            created_at__month=int(month),
            created_at__day=int(day),
        )
        .first()
    )
    if article:
        return render(request, "article.html", {"article": article})
    return HttpResponseNotFound()


def articles(request):
    return HttpResponseNotFound()
