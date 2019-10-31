import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from versatileimagefield.fields import VersatileImageField

from app.utils import is_email_organiser
from user.enums import UserType, SexType


class UserManager(BaseUserManager):
    def create_participant(
        self, email, name, surname, password, phone, birthday, sex, city, country
    ):
        if not email:
            raise ValueError("A user must have an email")

        user = self.model(
            email=email,
            name=name,
            surname=surname,
            type=UserType.PARTICIPANT.value,
            phone=phone,
            birthday=birthday,
            sex=sex,
            city=city,
            country=country,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        email,
        name,
        surname,
        type=UserType.PARTICIPANT.value,
        password=None,
        is_admin=False,
    ):
        if not email:
            raise ValueError("A user must have an email")

        user = self.model(
            email=email, name=name, surname=surname, type=type, is_admin=is_admin
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, surname, password):
        user = self.create_user(
            email, name, surname, UserType.ORGANISER.value, password, is_admin=True
        )
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(verbose_name="First name", max_length=255)
    surname = models.CharField(verbose_name="Last name", max_length=255)

    email_verified = models.BooleanField(default=False)
    verify_key = models.CharField(max_length=127, blank=True, null=True)
    verify_expiration = models.DateTimeField(default=timezone.now)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    type = models.PositiveSmallIntegerField(
        choices=((u.value, u.name) for u in UserType),
        default=UserType.PARTICIPANT.value,
    )
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Personal information
    picture = VersatileImageField("Image", default="user/picture/profile.png")
    picture_public_participants = models.BooleanField(default=True)
    picture_public_sponsors_and_recruiters = models.BooleanField(default=True)
    sex = models.PositiveSmallIntegerField(
        choices=((t.value, t.name) for t in SexType), default=SexType.NONE
    )
    birthday = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)

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
        return self.name + " " + self.surname

    def __str__(self):
        return self.full_name

    def get_dict(self):
        return {
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            "picture": self.picture,
            "picture_public_participants": self.picture_public_participants,
            "picture_public_sponsors_and_recruiters": self.picture_public_sponsors_and_recruiters,
            "sex": self.sex,
            "birthday": self.birthday,
            "phone": self.phone,
            "city": self.city,
            "country": self.country,
            "type": self.type,
        }

    def disable_verify(self):
        self.email_verified = False
        self.save()

    def update_verify(
        self, verify_key, verify_expiration=timezone.now() + timezone.timedelta(hours=1)
    ):
        self.verify_key = verify_key
        self.verify_expiration = verify_expiration
        self.save()

    def verify(self, verify_key):
        if timezone.now() <= self.verify_expiration and self.verify_key == verify_key:
            self.email_verified = True
            self.save()

    def mark_as_inactive(self):
        self.is_active = False
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
