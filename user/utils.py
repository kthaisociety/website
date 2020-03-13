from uuid import UUID

from user.models import User


def get_user_by_picture(picture):
    try:
        user_id = UUID(picture[:36])
        return User.objects.filter(id=user_id, is_active=True).first()
    except ValueError:
        return None


def get_organisers():
    return User.objects.organisers()
