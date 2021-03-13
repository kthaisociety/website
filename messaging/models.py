import uuid

from django.db import models


class SlackChannel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    is_general = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    topic = models.CharField(max_length=255, blank=True, null=True)
    purpose = models.CharField(max_length=255, blank=True, null=True)

    num_members = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    external_id = models.CharField(max_length=255, unique=True)
    external_created_at = models.DateTimeField()

    def __str__(self):
        return f"#{self.name}"
