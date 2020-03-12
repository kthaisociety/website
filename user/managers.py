from django.contrib.auth.base_user import BaseUserManager

from user.enums import UserType


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
        return super().get_queryset().filter(type=UserType.ORGANISER)
