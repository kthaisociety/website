from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from business.models import Tier, Offer
from business.enums import OfferTypeDict


def sponsor(request):
    tier_objs = Tier.objects.order_by("-price")
    return render(request, "sponsor.html", {"tiers": tier_objs})


def jobs(request):
    type = request.GET.get("type")
    offer_filters = Q(
        Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now()),
        is_visible=True,
        starts_at__lte=timezone.now(),
    )
    if type is not None:
        offer_filters &= Q(type=type)
    offers_objs = Offer.objects.filter(offer_filters).order_by("-created_at")
    return render(
        request,
        "jobs.html",
        {"offers": offers_objs, "types": OfferTypeDict, "type": type},
    )


def jobs_faq(request):
    return render(request, "jobs_faq.html")
