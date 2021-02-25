from django.apps import apps
from django.contrib.auth.base_user import BaseUserManager
from django.db.models import Subquery, OuterRef, CharField, BooleanField

from user.enums import UserType


class UserManager(BaseUserManager):
    def create_participant(
        self,
        email,
        name,
        surname,
        password,
        phone,
        birthday,
        gender,
        city,
        country,
        university,
        degree,
        graduation_year,
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
            gender=gender,
            city=city,
            country=country,
            university=university,
            degree=degree,
            graduation_year=graduation_year,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        email,
        name=None,
        surname=None,
        type=UserType.PARTICIPANT.value,
        password=None,
        is_admin=False,
    ):
        if not email:
            raise ValueError("A user must have an email")

        if not name and not surname:
            name = email.split("@")[0].capitalize()
            if "." in name:
                name = name.split(".")[0]
                surname = "".join(name.split(".")[1:])
            elif "_" in name:
                name = name.split("_")[0]
                surname = "".join(name.split("_")[1:])
            elif "-" in name:
                name = name.split(".")[0]
                surname = "".join(name.split(".")[1:])

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

    def organisers(self):
        return (
            super()
            .get_queryset()
            .filter(type=UserType.ORGANISER)
            .order_by("name", "surname")
        )

    def board(self):
        Role = apps.get_model("user", "Role")
        return (
            super()
            .get_queryset()
            .annotate(
                role_name=Subquery(
                    Role.objects.filter(
                        user_id=OuterRef("id"), ends_at__isnull=True
                    ).values("division__name")[:1],
                    output_field=CharField(),
                ),
                role_is_head=Subquery(
                    Role.objects.filter(
                        user_id=OuterRef("id"), ends_at__isnull=True, division__name=OuterRef("role_name")
                    ).values("is_head")[:1],
                    output_field=BooleanField(),
                ),
            )
            .filter(role_name__isnull=False)
            .order_by("name", "surname")
        )
