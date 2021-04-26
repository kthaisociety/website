from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from business.models import Tier, Offer


def sponsor(request):
    tier_objs = Tier.objects.order_by("-price")
    return render(request, "sponsor.html", {"tiers": tier_objs})


def jobs(request):
    offers_objs = Offer.objects.filter(
        Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now()),
        is_visible=True,
        starts_at__lte=timezone.now(),
    ).order_by("-created_at")
    return render(request, "jobs.html", {"offers": offers_objs})


def jobs_faq(request):
    return render(request, "jobs_faq.html")
