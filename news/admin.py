from django import forms
from django.contrib import admin, messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from messaging.api.slack.announcement import announce_article
from news.api.article.medium import import_medium_articles
from news.models import Article, Author, Fact, FactPost
from user.enums import UserType


def send_slack_announcement(modeladmin, request, articles):
    for article in articles:
        announce_article(article=article, creator_id=request.user.id)
    messages.success(
        request,
        f"Slack announcements have been posted for {articles.count()} article/s.",
    )


send_slack_announcement.short_description = "Send Slack announcement"


class AuthorForm(forms.ModelForm):
    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)

        self.fields["user"].queryset = (
            self.fields["user"]
            .queryset.filter(Q(is_author=True) | Q(type=UserType.ORGANISER))
            .order_by("name")
        )


class AuthorInline(admin.StackedInline):
    model = Author
    ordering = ("user__name",)
    show_change_link = True
    extra = 0
    form = AuthorForm


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    search_fields = ("id", "title", "subtitle", "slug", "body")
    list_display = ("title", "subtitle", "type", "status", "created_at")
    list_filter = ("type", "status")
    ordering = ("-created_at", "-updated_at", "title")
    readonly_fields = ("type",)
    actions = [send_slack_announcement]
    inlines = [AuthorInline]

    def get_urls(self):
        urls = super().get_urls()

        return [
            path(
                "import_medium_posts/",
                self.import_medium_posts,
                name="news_article_import_medium_posts",
            )
        ] + urls

    def import_medium_posts(self, request):
        success, created, updated = import_medium_articles()
        if success:
            messages.success(
                request,
                f"{created + updated} Medium posts have been correctly imported or updated.",
            )
        else:
            messages.error(request, f"Could not import any Medium posts.")
        return HttpResponseRedirect(reverse("admin:news_article_changelist"))


class FactPostInline(admin.StackedInline):
    model = FactPost
    display = ("type", "external_id", "created_at")
    ordering = ("-created_at",)
    show_change_link = False
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Fact)
class FactAdmin(admin.ModelAdmin):
    search_fields = ("id", "content")
    list_display = ("id", "content", "status", "picture", "created_at")
    ordering = ("-created_at",)
    inlines = [FactPostInline]
