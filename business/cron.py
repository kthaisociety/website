from django.utils import timezone

from business.models import Offer
from messaging.api.slack.announcement import announce_job_offers


def announce_latest_job_offers():
    job_offers = Offer.objects.filter(
        is_visible=True,
        starts_at__gte=timezone.now() - timezone.timedelta(days=7),
        starts_at__lt=timezone.now(),
    )
    if job_offers:
        announce_job_offers(job_offers=job_offers)