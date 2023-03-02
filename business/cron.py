from django.utils import timezone

from business.models import Offer
from messaging.api.slack.announcement import announce_job_offers


def announce_latest_job_offers():
    job_offers = (
        Offer.objects.filter(
            is_visible=True,
            starts_at__gte=timezone.now() - timezone.timedelta(days=1),
            starts_at__lt=timezone.now(),
        )
        .with_is_featured()
        .order_by("-is_featured", "created_at")
    )
    if job_offers:
        announce_job_offers(job_offers=job_offers)
