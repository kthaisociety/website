from page.models import Page


def get_page(category, code):
    return Page.objects.published().filter(category__code=category, code=code).first()
