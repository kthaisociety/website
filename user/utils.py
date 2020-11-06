import hashlib
from uuid import UUID

import requests
from django.utils.crypto import get_random_string

from app.settings import SL_TOKEN, SL_CHANNEL_GENERAL
from user.enums import GenderType
from user.models import User
from user.tasks import send_verify_email, send_password_email, send_imported_email


def get_user_by_email(email: str) -> User:
    return User.objects.filter(email=email).first()


def create_user(name: str, surname: str, email: str) -> User():
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
    return User.objects.organisers()


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


def slack_invite(user: User):
    if user.is_active and user.email_verified:
        if SL_TOKEN and SL_CHANNEL_GENERAL:
            requests.get(
                f"https://slack.com/api/users.admin.invite?token={SL_TOKEN}&email={user.email}&real_name={user.full_name}&channels={SL_CHANNEL_GENERAL}&resend=true"
            )
