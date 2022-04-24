from django.db import models

from news.enums import ArticleStatus


class ArticleManager(models.Manager):
    def published(self):
        return super().get_queryset().filter(status=ArticleStatus.PUBLISHED)
