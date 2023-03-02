from django.db.models import BooleanField, Case, Q, When
from django.shortcuts import render
from django.utils import timezone

from business.enums import OfferTypeDict
from business.models import Offer, Tier


def sponsor(request):
    tier_objs = Tier.objects.order_by("-price")
    return render(request, "sponsor.html", {"tiers": tier_objs})


def jobs(request):
    type = request.GET.get("type")
    offer_filters = Q(is_visible=True, starts_at__lte=timezone.now(),) & Q(
        Q(ends_at__isnull=True)
        | Q(ends_at__gt=timezone.now() - timezone.timedelta(days=10))
    )
    if type is not None:
        offer_filters &= Q(type=type)
    offers_objs = list(
        Offer.objects.filter(offer_filters)
        .annotate(
            is_offer_active=Case(
                When(ends_at__isnull=True, then=True),
                When(ends_at__gt=timezone.now(), then=True),
                default=False,
                output_field=BooleanField(),
            )
        )
        .with_is_featured()
        .order_by("-is_featured", "-is_offer_active", "-starts_at")
    )
    return render(
        request,
        "jobs.html",
        {"offers": offers_objs, "types": OfferTypeDict, "type": type},
    )


def jobs_faq(request):
    return render(request, "jobs_faq.html")
