from rest_framework import serializers

from .models import Donation, DonationClaim, RecoveryListing


class RecoveryListingSerializer(serializers.ModelSerializer):
    donor_name = serializers.SerializerMethodField()
    donor_id = serializers.IntegerField(source="donor.id", read_only=True)

    class Meta:
        model = RecoveryListing
        fields = [
            "id", "donor", "donor_id", "donor_name",
            "product", "title", "description", "quantity",
            "unit", "expiry_date", "pickup_location",
            "pickup_instructions", "status", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "donor", "donor_name", "status", "created_at", "updated_at"]

    def get_donor_name(self, obj):
        return obj.donor.get_full_name() or obj.donor.email


class RecoveryListingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecoveryListing
        fields = [
            "product", "title", "description", "quantity",
            "unit", "expiry_date", "pickup_location",
            "pickup_instructions",
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class DonationClaimSerializer(serializers.ModelSerializer):
    claimant_name = serializers.SerializerMethodField()
    listing_title = serializers.SerializerMethodField()

    class Meta:
        model = DonationClaim
        fields = [
            "id", "listing", "listing_title", "claimant",
            "claimant_name", "quantity", "notes", "status",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "claimant", "claimant_name", "listing_title", "status", "created_at", "updated_at"]

    def get_claimant_name(self, obj):
        return obj.claimant.get_full_name() or obj.claimant.email

    def get_listing_title(self, obj):
        return obj.listing.title


class DonationClaimCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationClaim
        fields = ["listing", "quantity", "notes"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class DonationSerializer(serializers.ModelSerializer):
    donor_name = serializers.SerializerMethodField()
    ngo_name = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = [
            "id", "donor", "donor_name", "amount", "ngo",
            "ngo_name", "message", "is_anonymous", "status",
            "created_at",
        ]
        read_only_fields = ["id", "donor", "donor_name", "ngo_name", "status", "created_at"]

    def get_donor_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.donor.get_full_name() or obj.donor.email

    def get_ngo_name(self, obj):
        if obj.ngo:
            return obj.ngo.get_full_name() or obj.ngo.email
        return None


class DonationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = ["amount", "ngo", "message", "is_anonymous"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
