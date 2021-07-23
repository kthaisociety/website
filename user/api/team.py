from typing import Optional, List

from user.models import Team


def get_teams() -> List[Team]:
    return Team.objects.order_by("-starts_at")


def get_team(code: Optional[str] = None) -> Team:
    if code:
        return Team.objects.filter(code=code).first()
    return Team.objects.order_by("-starts_at").first()
