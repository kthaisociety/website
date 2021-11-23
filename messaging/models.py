import uuid
from typing import Optional

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from messaging.enums import LogType
from user.models import User


class SlackChannel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    is_general = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    topic = models.CharField(max_length=255, blank=True, null=True)
    purpose = models.CharField(max_length=255, blank=True, null=True)

    num_members = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TODO: Should probably be unique but if missconfig and null then no more channels can be added
    external_id = models.CharField(max_length=255)
    external_creator_id = models.CharField(max_length=255)
    external_created_at = models.DateTimeField(auto_now_add=True)

    @property
    def creator(self) -> Optional[User]:
        return User.objects.filter(slack_id=self.external_creator_id).first()

    def __str__(self):
        return f"#{self.name}"


class SlackLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.PositiveSmallIntegerField(
        choices=((s.value, s.name) for s in LogType), default=LogType.ARTICLE.value
    )
    channel = models.ForeignKey(
        "SlackChannel",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="slack_logs",
    )
    creator = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="slack_logs",
        null=True,
        blank=True,
    )
    data = models.JSONField(default=dict, encoder=DjangoJSONEncoder)

    target_type = models.ForeignKey(
        ContentType,
        db_index=True,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="slack_logs",
    )
    target_id = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    target = GenericForeignKey("target_type", "target_id")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        owner = self.creator if self.creator else "System"
        return f"{LogType(self.type).name} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')} <{str(owner)}>"


class InteractiveMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slack_ts = models.CharField(max_length=255, db_index=True, null=False, blank=False)
    event = models.CharField(max_length=255, db_index=True, null=False, blank=False)
    diet = models.CharField(max_length=255, blank=True, null=True)
    diet_other = models.CharField(max_length=255, blank=True, null=True)
