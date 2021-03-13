import hashlib
from collections import OrderedDict
from typing import List
from uuid import UUID

import requests
from django.utils.crypto import get_random_string

from app.settings import SL_TOKEN, SL_CHANNEL_GENERAL, APP_ROLE_CHAIRMAN
from user.enums import GenderType
from user.models import User
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
    if user.is_active and user.email_verified:
        send_slack_email(user_id=user.id)


def send_created(user: User):
    verify_key = generate_verify_key(user)
    user.update_verify(verify_key=verify_key)
    send_created_email(user_id=user.id)
