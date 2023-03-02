from collections import defaultdict
from typing import Dict, List, Optional

from django.db.models import Q
from django.utils import timezone

from business.models import Offer, Sponsorship, Tier


def get_sponsorships() -> Dict[Tier, List[Sponsorship]]:
    sponsorships = defaultdict(list)
    for sponsorship in Sponsorship.objects.filter(
        Q(ends_at__isnull=True) | Q(ends_at__gte=timezone.now()), is_visible=True
    ).order_by("-tier__price", "starts_at"):
        sponsorships[sponsorship.tier].append(sponsorship)
    return dict(sponsorships)


def get_offers(is_featured: Optional[bool] = None) -> List[Offer]:
    offer_objs = Offer.objects.filter(
        Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now()),
        is_visible=True,
        starts_at__lte=timezone.now(),
    ).with_is_featured()
    if is_featured is not None:
        offer_objs = offer_objs.filter(is_featured=is_featured)
    return list(offer_objs.order_by("-is_featured", "created_at"))
