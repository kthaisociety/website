import uuid
from typing import Optional

from django.db import models

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
