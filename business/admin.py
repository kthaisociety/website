from django.contrib import admin

from business.models import Company, Contact, Tier, Sponsorship


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "code")
    list_display = ("name", "code", "website")
    ordering = ("-created_at", "-updated_at")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "surname", "email", "company", "user")
    list_display = ("name", "surname", "email", "company")
    list_filter = ("company",)
    ordering = ("-created_at", "-updated_at")


@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
    search_fields = ("id", "name", "code")
    list_display = ("name", "code", "price", "availability")
    ordering = ("-price",)


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    search_fields = ("id", "company", "tier")
    list_display = ("company", "tier", "starts_at", "ends_at", "is_visible")
    list_filter = ("company", "tier")
    ordering = ("-starts_at", "company")
