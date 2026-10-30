from django.contrib import admin

from .models import Donation, DonationClaim, RecoveryListing


@admin.register(RecoveryListing)
class RecoveryListingAdmin(admin.ModelAdmin):
    list_display = ["title", "donor", "quantity", "unit", "status", "expiry_date", "created_at"]
    list_filter = ["status", "unit"]
    search_fields = ["title", "donor__email", "donor__username", "pickup_location"]
    raw_id_fields = ["donor", "product"]
    date_hierarchy = "created_at"


@admin.register(DonationClaim)
class DonationClaimAdmin(admin.ModelAdmin):
    list_display = ["listing", "claimant", "quantity", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["listing__title", "claimant__email", "claimant__username"]
    raw_id_fields = ["listing", "claimant"]
    date_hierarchy = "created_at"


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ["donor", "amount", "ngo", "status", "created_at"]
    list_filter = ["status", "is_anonymous"]
    search_fields = ["donor__email", "donor__username", "message"]
    raw_id_fields = ["donor", "ngo"]
    date_hierarchy = "created_at"
