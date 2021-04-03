from django.contrib import admin, messages

from messaging.api.slack.announcement import announce_article
from news.models import Article


def send_slack_announcement(modeladmin, request, articles):
    for article in articles:
        announce_article(article=article, creator_id=request.user.id)
    messages.success(
        request,
        f"Slack announcements have been posted for {articles.count()} article/s.",
    )


send_slack_announcement.short_description = "Send Slack announcement"


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    search_fields = ("id", "title", "subtitle", "slug", "body")
    list_display = ("title", "subtitle", "status")
    list_filter = ("status",)
    ordering = ("-created_at", "-updated_at", "title")
    actions = [send_slack_announcement]
