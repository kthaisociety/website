import urllib.request
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from versatileimagefield.fields import VersatileImageField

from page.enums import PageContentType, PageSourceType, PageStatus
from page.managers import PageManager


class Page(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    category = models.ForeignKey("Category", on_delete=models.PROTECT)
    code = models.CharField(max_length=31)
    content_plain = models.TextField(blank=True, null=True)
    content_html = models.TextField(blank=True, null=True)
    content_markdown = models.TextField(blank=True, null=True)
    content_markdown_url = models.CharField(max_length=255, blank=True, null=True)
    status = models.PositiveSmallIntegerField(
        choices=((s.value, s.name) for s in PageStatus), default=PageStatus.DRAFT.value
    )
    picture = VersatileImageField(
        "Image", upload_to="page/page/", blank=True, null=True
    )
    in_menu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PageManager()

    @property
    def content(self):
        if self.content_plain:
            return self.content_plain, PageContentType.PLAIN, PageSourceType.INTERNAL
        elif self.content_html:
            return self.content_html, PageContentType.HTML, PageSourceType.INTERNAL
        elif self.content_markdown:
            return (
                self.content_markdown,
                PageContentType.MARKDOWN,
                PageSourceType.INTERNAL,
            )
        return (
            urllib.request.urlopen(self.content_markdown_url).read().decode("utf-8"),
            PageContentType.MARKDOWN,
            PageSourceType.URL,
        )

    @property
    def url(self):
        return reverse(
            "page_page", kwargs=dict(category=self.category.code, code=self.code)
        )

    class Meta:
        unique_together = ("category", "code")

    def clean(self):
        messages = dict()
        if (
            sum(
                (1 if content else 0)
                for content in [
                    self.content_plain,
                    self.content_html,
                    self.content_markdown,
                    self.content_markdown_url,
                ]
            )
            != 1
        ):
            message = (
                "You must ONLY FILL ONE plain, HTML, markdown content or markdown URL"
            )
            messages["content_plain"] = message
            messages["content_html"] = message
            messages["content_markdown"] = message
            messages["content_markdown_url"] = message
        if messages:
            raise ValidationError(messages)

    def __str__(self):
        return self.title


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=31, unique=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Categories"


class Picture(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    picture = VersatileImageField("Image", upload_to="page/picture/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
