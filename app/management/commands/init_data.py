from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand
from django.db import transaction

from app.settings import PERMISSION_GROUPS, PERMISSIONS_COMMON


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        # Create groups
        for group, permissions in PERMISSION_GROUPS.items():
            group, _ = Group.objects.get_or_create(name=group)
            for t, app_ps in PERMISSIONS_COMMON.items():
                for app, ps in app_ps.items():
                    for p in ps:
                        group.permissions.add(
                            Permission.objects.get(
                                content_type__app_label=app, codename=f"{t}_{p}"
                            )
                        )
            for t, app_ps in permissions.items():
                for app, ps in app_ps.items():
                    for p in ps:
                        group.permissions.add(
                            Permission.objects.get(
                                content_type__app_label=app, codename=f"{t}_{p}"
                            )
                        )
