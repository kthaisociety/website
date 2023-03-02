from django.apps import apps
from django.db.models import BooleanField, Case, Exists, OuterRef, QuerySet, When
from django.utils import timezone


class SponsorshipQuerySet(QuerySet):
    def with_is_active(self):
        return self.annotate(
            is_active=Case(
                When(ends_at__isnull=True, is_visible=True, then=True),
                When(ends_at__gte=timezone.now(), is_visible=True, then=True),
                output_field=BooleanField(),
                default=False,
            )
        )


class OfferQuerySet(QuerySet):
    def with_is_featured(self):
        Sponsorship = apps.get_model("business", "Sponsorship")

        return self.annotate(
            is_featured=Exists(
                Sponsorship.objects.filter(company_id=OuterRef("company_id"))
                .with_is_active()
                .filter(is_active=True)
            )
        )
