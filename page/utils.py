from typing import List, Dict

from page.enums import PageStatus
from page.models import Page, Category


def get_page(category, code):
    return Page.objects.published().filter(category__code=category, code=code).first()


def get_menu_pages() -> Dict[Category, List[Page]]:
    pages = Page.objects.filter(in_menu=True, status=PageStatus.PUBLISHED).order_by(
        "category", "title"
    )
    categories = {c: [] for c in Category.objects.filter(page__in=pages)}
    for page in pages:
        categories[page.category].append(page)
    return categories
