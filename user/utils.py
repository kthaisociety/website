import hashlib
from collections import OrderedDict
from io import BytesIO, StringIO
from typing import List
from uuid import UUID
import csv
import zipfile

import requests
from django.utils.crypto import get_random_string

from app.settings import SL_TOKEN, SL_CHANNEL_GENERAL, APP_ROLE_CHAIRMAN
from event.enums import RegistrationStatus
from user.enums import GenderType, UserType
from user.models import User, History
from user.tasks import (
    send_verify_email,
    send_password_email,
    send_imported_email,
    send_slack_email,
    send_created_email,
)


def get_user_by_email(email: str) -> User:
    return User.objects.filter(email=email).first()


def get_users() -> List[User]:
    return User.objects.all()


def create_user(name: str, surname: str, email: str) -> User:
    user = User.objects.create_participant(
        name=name,
        surname=surname,
        email=email,
        password=None,
        phone=None,
        birthday=None,
        gender=GenderType.NONE,
        city=None,
        country=None,
        university=None,
        degree=None,
        graduation_year=None,
    )
    user.registration_finished = False
    user.save()
    return user


def get_user_by_picture(picture):
    try:
        user_id = UUID(picture[:36])
        return User.objects.filter(id=user_id, is_active=True).first()
    except ValueError:
        return None


def get_organisers():
    return sorted(
        [u for u in User.objects.organisers() if u.role],
        key=lambda u: (
            not u.role.division.name.lower() == APP_ROLE_CHAIRMAN.lower(),
            u.role.division.name,
            not u.role.is_head,
        ),
    )


def get_board():
    board = User.objects.board()
    role_names = {user.role_name for user in board}
    return OrderedDict(
        [
            (
                role_name,
                sorted(
                    [user for user in board if user.role_name == role_name],
                    key=lambda u: (not u.role_is_head, u.name, u.surname),
                ),
            )
            for role_name in sorted(list(role_names))
        ]
    )


def get_histories():
    return History.objects.all().order_by("-time")


def generate_verify_key(user: User):
    chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    secret_key = get_random_string(32, chars)
    return hashlib.sha256((secret_key + user.email).encode("utf-8")).hexdigest()


def send_verify(user: User):
    user.disable_verify()
    verify_key = generate_verify_key(user)
    user.update_verify(verify_key=verify_key)
    send_verify_email(user_id=user.id)


def send_password(user: User):
    verify_key = generate_verify_key(user)
    user.update_verify(verify_key=verify_key)
    send_password_email(user_id=user.id)


def send_imported(user: User):
    verify_key = generate_verify_key(user)
    user.update_verify(verify_key=verify_key)
    send_imported_email(user_id=user.id)


def send_slack(user: User):
    if not user.slack_id:
        send_slack_email(user_id=user.id)


def send_created(user: User):
    verify_key = generate_verify_key(user)
    user.update_verify(verify_key=verify_key)
    send_created_email(user_id=user.id)


def get_user_data_zip(user_id: UUID) -> BytesIO:
    user = User.objects.get(id=user_id)

    user_csv = StringIO()
    csvwriter = csv.writer(
        user_csv, delimiter=";", quotechar="|", quoting=csv.QUOTE_MINIMAL
    )
    csvwriter.writerow(["ID", user_id])
    csvwriter.writerow(["Created at", user.created_at])
    csvwriter.writerow(["Updated at", user.updated_at])
    csvwriter.writerow(["First name", user.name])
    csvwriter.writerow(["Last name", user.surname])
    csvwriter.writerow(["Email", user.email])
    csvwriter.writerow(["Email verified", user.email_verified])
    csvwriter.writerow(["Registration finished", user.registration_finished])
    csvwriter.writerow(["Last login", user.last_login])
    csvwriter.writerow(["Type", UserType(user.type).name.upper()])
    csvwriter.writerow(["Gender", GenderType(user.gender).name.upper()])
    csvwriter.writerow(["Birthday", user.birthday])
    csvwriter.writerow(["Phone", user.phone])
    csvwriter.writerow(["City", user.city])
    csvwriter.writerow(["Country", user.country])
    csvwriter.writerow(["University", user.university])
    csvwriter.writerow(["Programme", user.degree])
    csvwriter.writerow(["Graduation year", user.graduation_year])
    csvwriter.writerow(["Website", user.website])
    csvwriter.writerow(["Slack ID", user.slack_id])
    csvwriter.writerow(["Slack name", user.slack_display_name])
    csvwriter.writerow(
        [
            "Slack status",
            (
                f"{user.slack_status_emoji} {user.slack_status_text}"
                if user.slack_status_text
                else ""
            ),
        ]
    )

    registrations_csv = StringIO()
    csvwriter = csv.writer(
        registrations_csv, delimiter=";", quotechar="|", quoting=csv.QUOTE_MINIMAL
    )
    csvwriter.writerow(["ID", "Event", "Status", "Created at", "Updated at"])

    for registration in user.registrations.all():
        csvwriter.writerow(
            [
                registration.id,
                str(registration.event),
                RegistrationStatus(registration.status).name.upper(),
                registration.created_at,
                registration.updated_at,
            ]
        )

    mf = BytesIO()
    zf = zipfile.ZipFile(mf, mode="w", compression=zipfile.ZIP_DEFLATED)
    zf.writestr("user/user.csv", user_csv.getvalue())
    picture_extension = user.picture.name.split(".")[-1]
    zf.writestr(f"user/profile.{picture_extension}", user.picture.read())
    if user.slack_picture:
        slack_extension = user.slack_picture.name.split(".")[-1]
        zf.writestr(f"user/slack.{slack_extension}", user.slack_picture.read())
    if user.resume:
        resume_extension = user.resume.name.split(".")[-1]
        zf.writestr(f"user/resume.{resume_extension}", user.resume.read())
    if user.registrations.exists():
        zf.writestr(f"registration/registration.csv", registrations_csv.getvalue())
    zf.close()

    return mf

def delete_user_account(user_id:str) -> None:
    User.objects.filter(id=user_id).delete()
