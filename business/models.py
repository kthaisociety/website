import textwrap
import uuid

import markdown
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from versatileimagefield.fields import VersatileImageField

from business.enums import OfferType


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True, unique=True)
    logo = VersatileImageField("Logo", upload_to="business/company/logo/")
    website = models.URLField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super().save()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "companies"
        ordering = ["name"]


class Contact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(verbose_name="First name", max_length=255)
    surname = models.CharField(verbose_name="Last name", max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    company = models.ForeignKey(
        "Company", on_delete=models.PROTECT, related_name="contacts"
    )
    user = models.OneToOneField(
        "user.User",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="contact",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return self.name + " " + self.surname

    def __str__(self):
        if self.user:
            return str(self.user)
        return f"{self.full_name} <{self.email}>"


class Tier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(max_length=5000)
    availability = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super().save()

    def __str__(self):
        return self.name


class Sponsorship(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        "Company", on_delete=models.PROTECT, related_name="sponsorships"
    )
    tier = models.OneToOneField(
        "Tier",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sponsorships",
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(blank=True, null=True)
    is_visible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{str(self.tier)} <{str(self.company)}>"


class Offer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    company = models.ForeignKey(
        "Company", on_delete=models.PROTECT, related_name="offers"
    )
    type = models.PositiveSmallIntegerField(
        choices=((ot.value, ot.name) for ot in OfferType),
        default=OfferType.INTERNSHIP.value,
    )
    description = models.TextField(max_length=5000, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(max_length=200, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(blank=True, null=True)
    is_visible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_current(self):
        return timezone.now() >= self.starts_at and (
            not self.ends_at or timezone.now() < self.ends_at
        )

    @property
    def is_new(self):
        return self.starts_at >= timezone.now() - timezone.timedelta(days=7)

    @property
    def description_plaintext(self):
        html = markdown.markdown(self.description)
        return "".join(BeautifulSoup(html, "html.parser").findAll(text=True))

    @property
    def description_extra_short(self):
        return textwrap.shorten(
            self.description_plaintext, width=125, placeholder="..."
        )

    @property
    def description_short(self):
        return textwrap.shorten(
            self.description_plaintext, width=250, placeholder="..."
        )

    @property
    def our_url(self):
        return reverse("business_jobs") + f"#{self.id}"

    def __str__(self):
        return f"{self.title} <{str(self.company)}>"

    def clean(self):
        messages = dict()
        if not self.url and not self.email:
            messages["url"] = "Either the application URL or email has to be provided"
        if messages:
            raise ValidationError(messages)
