from typing import List, Optional

from django.db.models import Prefetch

from user.models import Division, Role, Team


def get_teams() -> List[Team]:
    return Team.objects.order_by("-starts_at")


def get_team(code: Optional[str] = None) -> Team:
    team_prefetch = Prefetch(
        "division_set",
        Division.objects.prefetch_related(
            Prefetch(
                "role_set",
                Role.objects.select_related("user").order_by("-is_head", "-user"),
                to_attr="roles",
            )
        ).order_by("display_name"),
        to_attr="divisions",
    )
    if code:
        return Team.objects.filter(code=code).prefetch_related(team_prefetch).first()
    return Team.objects.prefetch_related(team_prefetch).order_by("-starts_at").first()
