from django.contrib import admin

from news.models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    search_fields = ("id", "title", "subtitle", "slug", "body")
    list_display = ("title", "subtitle", "status")
    list_filter = ("status",)
    ordering = ("-created_at", "-updated_at", "title")
