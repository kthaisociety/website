from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from business.models import Tier, Offer
from business.enums import OfferTypeDict


def sponsor(request):
    tier_objs = Tier.objects.order_by("-price")
    return render(request, "sponsor.html", {"tiers": tier_objs})


def jobs(request):
    type = request.GET.get("type", '')
    if type == '':
        offers_objs = Offer.objects.filter(
            Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now()),
            is_visible=True,
            starts_at__lte=timezone.now(),
        ).order_by("-created_at")
    else:
        offers_objs = Offer.objects.filter(
            Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now()),
            is_visible=True,
            starts_at__lte=timezone.now(),
            type=type
        ).order_by("-created_at")
    return render(request, "jobs.html", {"offers": offers_objs, "types": OfferTypeDict})


def jobs_faq(request):
    return render(request, "jobs_faq.html")
