from django.http import HttpResponseNotFound
from django.shortcuts import render

from page.utils import get_page


def page(request, category, code):
    page = get_page(category, code)
    if page:
        return render(request, "page.html", {"page": page})
    return HttpResponseNotFound()
