import hashlib
from uuid import UUID

from django.utils.crypto import get_random_string

from user.models import User
from user.tasks import send_verify_email, send_password_email, send_imported_email


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
