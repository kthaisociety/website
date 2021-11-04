import hashlib
import os
import re
import uuid
from typing import Optional

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.functional import cached_property
from versatileimagefield.fields import VersatileImageField

from app.storage import OverwriteStorage
from app.utils import is_email_organiser
from user.consts import EMOJIS
from user.enums import UserType, GenderType, DietType
from user.managers import UserManager


def validate_orcid(value):
    if value and not re.match(r"^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}$", value):
        raise ValidationError(f"{value} is not a valid ORCID.")


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(verbose_name="First name", max_length=255)
    surname = models.CharField(
        verbose_name="Last name", max_length=255, blank=True, null=True
    )

    email_verified = models.BooleanField(default=False)
    verify_key = models.CharField(max_length=127, blank=True, null=True)
    verify_expiration = models.DateTimeField(default=timezone.now)

    registration_finished = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    type = models.PositiveSmallIntegerField(
        choices=((u.value, u.name) for u in UserType),
        default=UserType.PARTICIPANT.value,
    )
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_author = models.BooleanField(default=False)
    is_forgotten = models.BooleanField(default=False)
    is_subscriber = models.BooleanField(default=True)

    # Personal information
    picture = VersatileImageField(
        "Image",
        upload_to="user/picture/",
        default="user/picture/profile.png",
        storage=OverwriteStorage(),
    )
    gender = models.PositiveSmallIntegerField(
        choices=((t.value, t.name) for t in GenderType), default=GenderType.NONE
    )
    birthday = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)

    # University
    university = models.CharField(max_length=255, blank=True, null=True)
    degree = models.CharField(max_length=255, blank=True, null=True)
    graduation_year = models.PositiveIntegerField(
        default=timezone.now().year, blank=True, null=True
    )

    # Details
    website = models.CharField(max_length=255, blank=True, null=True)
    resume = models.FileField(upload_to="user/resume/", blank=True, null=True)

    # Social networks
    linkedin_url = models.URLField(max_length=200, blank=True, null=True)
    twitter_url = models.URLField(max_length=200, blank=True, null=True)
    github_url = models.URLField(max_length=200, blank=True, null=True)
    scholar_url = models.URLField(max_length=200, blank=True, null=True)
    researchgate_url = models.URLField(max_length=200, blank=True, null=True)
    orcid = models.CharField(
        max_length=255, validators=[validate_orcid], blank=True, null=True
    )

    # Slack
    # TODO: Should somehow be unique if not null
    slack_id = models.CharField(max_length=255, blank=True, null=True)
    slack_token = models.CharField(max_length=255, blank=True, null=True)
    slack_scopes = models.CharField(max_length=255, blank=True, null=True)
    slack_status_text = models.CharField(max_length=255, blank=True, null=True)
    slack_status_emoji = models.CharField(max_length=255, blank=True, null=True)
    slack_display_name = models.CharField(max_length=255, blank=True, null=True)
    slack_picture = VersatileImageField(
        "Slack image",
        upload_to="user/slack/picture/",
        blank=True,
        null=True,
        storage=OverwriteStorage(),
    )
    slack_picture_hash = models.CharField(max_length=255, blank=True, null=True)

    # Dietary restrictions
    diet = models.CharField(max_length=255, blank=True, null=True)
    diet_other = models.CharField(max_length=255, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    @property
    def dietary_restrictions(self):
        if not self.diet:
            return []
        diets = re.sub(r"[^0-9,]", "", self.diet).split(",")
        diet_types = set()
        for diet in diets:
            if diet != "":
                diet_types.add(DietType(int(diet)))
        return diet_types

    @property
    def profile_picture(self):
        if self.slack_picture:
            return self.slack_picture
        return self.picture

    @property
    def slack_status(self):
        if self.slack_status_emoji:
            try:
                emoji = (
                    EMOJIS[self.slack_status_emoji[1:-1]]
                    .encode("utf-16", "surrogatepass")
                    .decode("utf-16")
                )
                return f"{emoji} {self.slack_status_text}"
            except KeyError:
                return f"{self.slack_status_text}"
        else:
            return ""

    @property
    def is_organiser(self):
        return self.type == UserType.ORGANISER.value

    @property
    def is_participant(self):
        return self.type == UserType.PARTICIPANT.value

    @property
    def is_staff(self):
        return self.is_admin

    @cached_property
    def role(self):
        return self.role_set.filter(ends_at__isnull=True).order_by("-is_head").first()

    @cached_property
    def event_registrations(self):
        return self.registrations.order_by("-created_at").all()

    @property
    def full_name(self):
        if self.surname:
            return self.name + " " + self.surname
        return self.name

    @property
    def subscriber_id(self):
        return hashlib.md5(self.email.lower().encode("utf-8")).hexdigest()

    def __str__(self):
        if self.full_name:
            return f"{self.full_name} <{self.email}>"
        return f"<{self.email}>"

    def get_dict(self):
        return {
            "name": self.name,
            "surname": self.surname,
            "full_name": self.full_name,
            "email": self.email,
            "picture": self.picture,
            "gender": self.gender,
            "birthday": self.birthday,
            "phone": self.phone,
            "city": self.city,
            "country": self.country,
            "type": self.type,
            "description": (self.description if self.description else ""),
            "website": (self.website if self.website else ""),
        }

    def disable_verify(self):
        self.email_verified = False
        self.save()

    def update_verify(
        self, verify_key, verify_expiration: Optional[timezone.datetime] = None
    ):
        if not verify_expiration:
            verify_expiration = timezone.now() + timezone.timedelta(days=1)

        self.verify_key = verify_key
        self.verify_expiration = verify_expiration
        self.save()

    def delete_verify_key(self):
        self.verify_key = None
        self.save()

    def verify(self, verify_key):
        if timezone.now() <= self.verify_expiration and self.verify_key == verify_key:
            self.email_verified = True
            self.delete_verify_key()
            self.save()

            from user.utils import send_slack

            send_slack(user=self)

    def mark_as_inactive(self):
        self.is_active = False
        self.save()

    def finish_registration(
        self,
        name,
        surname,
        phone,
        university,
        degree,
        graduation_year,
        birthday,
        gender,
        city,
        country,
    ):
        self.name = name
        self.surname = surname
        self.phone = phone
        self.university = university
        self.degree = degree
        self.graduation_year = graduation_year
        self.birthday = birthday
        self.gender = gender
        self.city = city
        self.country = country
        self.registration_finished = True
        self.save()

    def forget(self) -> Optional["User"]:
        if self.type != UserType.PARTICIPANT:
            return

        if not self.email_verified:
            return

        self.email = "forgoten_" + str(self.id) + "@member.kthais.com"
        self.name = "Forgotten"
        self.username = "User"

        if self.picture and self.picture.path.split("/")[-1] != "profile.png":
            self.picture.delete_all_created_images()
            self.picture.delete(save=False)

        self.gender = GenderType.NONE
        self.birthday = None
        self.phone = None
        self.city = None
        self.country = None

        self.university = None
        self.degree = None
        self.graduation_year = None

        self.website = None
        if self.resume:
            self.resume.delete(save=False)
        self.linkedin_url = None
        self.twitter_url = None
        self.github_url = None
        self.scholar_url = None
        self.researchgate_url = None
        self.orcid = None

        self.slack_id = None
        self.slack_token = None
        self.slack_scopes = None
        self.slack_status_text = None
        self.slack_status_emoji = None
        self.slack_display_name = None
        if self.slack_picture:
            self.slack_picture.delete_all_created_images()
            self.slack_picture.delete(save=False)
        self.slack_picture_hash = None  # TODO Delete file

        self.is_active = False
        self.is_forgotten = True

        self.diet = None
        self.diet_other = None

        return self.save()

    @property
    def resume_name(self):
        return os.path.basename(self.resume.name)

    def clean(self):
        messages = dict()
        # TODO: Check properly if 14 already or not
        if self.birthday and (
            timezone.now().date() - self.birthday
        ) < timezone.timedelta(days=14 * 365):
            messages["age"] = "The minimum age is 14"
        if messages:
            raise ValidationError(messages)

    def save(self, *args, **kwargs):
        self.clean()
        if is_email_organiser(self.email):
            self.type = UserType.ORGANISER.value

        if self.email_verified and self.registration_finished:
            import user.api.newsletter

            transaction.on_commit(
                lambda: user.api.newsletter.update_newsletter_list(user_id=self.id)
            )

        return super().save(*args, **kwargs)


class GoogleUser(User):
    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.clean()
        self.email_verified = True
        return super().save(*args, **kwargs)


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(blank=True, null=True)
    code = models.CharField(max_length=255, blank=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Team {self.code.upper() or self.starts_at.strftime('%Y')}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(self.starts_at.year)
        super().save(*args, **kwargs)


class Division(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True)
    team = models.ForeignKey("Team", on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.display_name} <{str(self.team)}>"

    class Meta:
        ordering = ["display_name"]


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("User", on_delete=models.PROTECT)
    division = models.ForeignKey("Division", on_delete=models.PROTECT)
    is_head = models.BooleanField(default=False)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(blank=True, null=True)
    picture = VersatileImageField(
        "Image", upload_to="user/role/picture/", default="user/role/picture/profile.png"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active(self):
        if self.ends_at:
            return self.starts_at <= timezone.now() < self.ends_at
        return timezone.now() >= self.starts_at

    def __str__(self):
        return f"{self.user} <{str(self.division.name)}>"

    class Meta:
        ordering = ["user"]


class History(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    body = models.TextField(max_length=5000)
    time = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "histories"
