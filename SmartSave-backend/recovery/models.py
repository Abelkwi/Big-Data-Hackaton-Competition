from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class RecoveryListing(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("claimed", "Claimed"),
        ("completed", "Completed"),
        ("expired", "Expired"),
    ]
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recovery_listings")
    product = models.ForeignKey("marketplace.Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="recovery_listings")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default="kg")
    expiry_date = models.DateField(null=True, blank=True)
    pickup_location = models.CharField(max_length=255)
    pickup_instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["donor", "-created_at"])]
    def __str__(self):
        return self.title


class DonationClaim(models.Model):
    STATUS_CHOICES = [("pending","Pending"),("approved","Approved"),("collected","Collected"),("completed","Completed"),("cancelled","Cancelled")]
    listing = models.ForeignKey(RecoveryListing, on_delete=models.CASCADE, related_name="claims")
    claimant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="donation_claims")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["listing", "claimant"])]
    def __str__(self):
        return f"Claim by {self.claimant.email} on {self.listing.title}"


class Donation(models.Model):
    STATUS_CHOICES = [("pending","Pending"),("completed","Completed"),("failed","Failed")]
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="monetary_donations")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    ngo = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ngo_donations")
    message = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["donor", "-created_at"])]
    def __str__(self):
        return f"Donation {self.amount} by {self.donor.email}"
