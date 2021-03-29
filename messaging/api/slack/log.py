from typing import Optional
from uuid import UUID

from django.db.models import Model

from messaging.enums import LogType
from messaging.models import SlackLog


def create(
    type: LogType,
    target: Model,
    channel_id: UUID,
    user_id: UUID = None,
    data: Optional[dict] = None,
):
    return SlackLog.objects.create(
        type=type,
        channel_id=channel_id,
        user_id=user_id,
        data=data or {},
        target=target,
    )
