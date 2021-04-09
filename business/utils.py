from collections import defaultdict
from typing import List, Dict

from django.db.models import Q
from django.utils import timezone

from business.models import Sponsorship, Tier


def get_sponsorships() -> Dict[Tier, List[Sponsorship]]:
    sponsorships = defaultdict(list)
    for sponsorship in Sponsorship.objects.filter(
        Q(ends_at__isnull=True) | Q(ends_at__gte=timezone.now()), is_visible=True
    ).order_by("-tier__price", "starts_at"):
        sponsorships[sponsorship.tier].append(sponsorship)
    return dict(sponsorships)