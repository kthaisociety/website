import re
import textwrap
import uuid

import markdown
from bs4 import BeautifulSoup
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from versatileimagefield.fields import VersatileImageField

from news.enums import ArticleStatus, ArticleType
from news.managers import ArticleManager


class Article(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    slug = models.CharField(max_length=255, blank=True, unique=True)
    picture = VersatileImageField("Image", upload_to="news/article/")
    body = models.TextField()
    type = models.PositiveSmallIntegerField(
        choices=((s.value, s.name) for s in ArticleType),
        default=ArticleType.REGULAR.value,
    )
    status = models.PositiveSmallIntegerField(
        choices=((s.value, s.name) for s in ArticleStatus),
        default=ArticleStatus.DRAFT.value,
    )
    external_url = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ArticleManager()

    @property
    def description_extra_short(self):
        return textwrap.shorten(self.body_plaintext, width=125, placeholder="...")

    @property
    def description_short(self):
        return textwrap.shorten(self.body_plaintext, width=250, placeholder="...")

    @property
    def description_paragraph(self):
        return self.body_plaintext.partition("\n")[0]

    @property
    def lead(self):
        if self.subtitle:
            return self.subtitle
        return self.description_extra_short

    @property
    def url(self):
        if self.type == ArticleType.MEDIUM and self.external_url:
            return self.external_url
        return reverse(
            "news_article",
            kwargs=dict(
                year=self.created_at.strftime("%Y"),
                month=self.created_at.strftime("%m"),
                day=self.created_at.strftime("%d"),
                slug=self.slug,
            ),
        )

    @property
    def body_plaintext(self):
        html = markdown.markdown(self.body)
        return "".join(BeautifulSoup(html, "html.parser").findAll(text=True))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save()

    def __str__(self):
        return self.title


class Author(models.Model):
    article = models.ForeignKey(
        "news.Article", on_delete=models.PROTECT, related_name="authors"
    )
    user = models.ForeignKey(
        "user.User", on_delete=models.PROTECT, related_name="authorships"
    )
