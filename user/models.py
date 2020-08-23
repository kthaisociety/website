import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from versatileimagefield.fields import VersatileImageField

from app.utils import is_email_organiser
from user.enums import UserType, GenderType
from user.managers import UserManager


class User(AbstractBaseUser):
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

    # Personal information
    picture = VersatileImageField(
        "Image", upload_to="user/picture/", default="user/picture/profile.png"
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
    description = models.CharField(max_length=255, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    @property
    def is_organiser(self):
        return self.type == UserType.ORGANISER.value

    @property
    def is_participant(self):
        return self.type == UserType.PARTICIPANT.value

    @property
    def is_staff(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def full_name(self):
        if self.surname:
            return self.name + " " + self.surname
        return self.name

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
        self, verify_key, verify_expiration=timezone.now() + timezone.timedelta(days=1)
    ):
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

            from user.utils import slack_invite
            slack_invite(user=self)

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
        return super().save(*args, **kwargs)


class GoogleUser(User):
    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.clean()
        self.email_verified = True
        return super().save(*args, **kwargs)
