from django.shortcuts import render

from business.models import Tier


def sponsor(request):
    tier_objs = Tier.objects.order_by("-price")
    return render(request, "sponsor.html", {"tiers": tier_objs})
