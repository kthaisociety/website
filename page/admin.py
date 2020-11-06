from django.contrib import admin

from page.models import Page, Category, Picture


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    search_fields = (
        "id",
        "title",
        "code",
        "category",
        "content_plain",
        "content_html",
        "content_markdown",
        "content_url_markdown",
    )
    list_display = ("title", "category", "code")
    ordering = ("title",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("id", "title", "code")
    list_display = ("title", "code")
    ordering = ("title",)


@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    search_fields = ("id",)
    list_display = ("picture",)
    ordering = ("picture",)
