from django.db import models

from page.enums import PageStatus


class PageManager(models.Manager):
    def published(self):
        return super().get_queryset().filter(status=PageStatus.PUBLISHED)
