from typing import Optional
from uuid import UUID

from django.db.models import Model

from messaging.enums import LogType
from messaging.models import SlackLog


def find(**filters):
    return SlackLog.objects.filter(**filters)


def create(
    type: LogType,
    target: Model,
    channel_id: UUID = None,
    creator_id: UUID = None,
    data: Optional[dict] = None,
):
    return SlackLog.objects.create(
        type=type,
        channel_id=channel_id,
        creator_id=creator_id,
        data=data or {},
        target=target,
    )
