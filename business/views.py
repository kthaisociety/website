from django.shortcuts import render

from business.models import Tier


def tiers(request):
    tier_objs = Tier.objects.order_by("-price")
    return render(request, "tiers.html", {"tiers": tier_objs})
