from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Profile, FarmerProfile, BuyerProfile, NGOProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "is_verified",
            "phone",
            "date_joined",
        ]
        read_only_fields = ["id", "is_verified", "date_joined"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "first_name",
            "last_name",
            "gender",
            "profile_photo",
            "bio",
            "country",
            "province",
            "district",
            "sector",
            "cell",
            "village",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FarmerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        fields = [
            "id",
            "farm_name",
            "farm_size",
            "main_crop",
            "experience",
            "certificate",
            "gps_latitude",
            "gps_longitude",
            "store_name",
            "store_slug",
            "store_banner",
            "store_description",
            "website",
            "facebook",
            "instagram",
            "twitter",
        ]
        read_only_fields = ["id", "store_slug"]


class BuyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerProfile
        fields = [
            "id",
            "company_name",
            "buyer_type",
            "supply_needs",
            "monthly_volume",
            "delivery_frequency",
            "registration_number",
        ]
        read_only_fields = ["id"]


class NGOProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NGOProfile
        fields = [
            "id",
            "organization_name",
            "organization_type",
            "slug",
            "registration_number",
            "website",
            "mission",
            "focus_areas",
            "beneficiaries_served",
            "collection_capacity",
            "has_transport",
            "food_types",
            "beneficiaries_served",
            "collection_capacity",
            "has_transport",
            "food_types",
            "is_approved",
        ]
        read_only_fields = ["id", "slug", "is_approved"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    google_credential = serializers.CharField(write_only=True, required=False)
    province = serializers.CharField(write_only=True, required=False, allow_blank=True)
    district = serializers.CharField(write_only=True, required=False, allow_blank=True)
    sector = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cell = serializers.CharField(write_only=True, required=False, allow_blank=True)
    village = serializers.CharField(write_only=True, required=False, allow_blank=True)
    farm_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    farm_size = serializers.CharField(write_only=True, required=False, allow_blank=True)
    main_crop = serializers.CharField(write_only=True, required=False, allow_blank=True)
    company_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    buyer_type = serializers.CharField(write_only=True, required=False, allow_blank=True)
    supply_needs = serializers.CharField(write_only=True, required=False, allow_blank=True)
    monthly_volume = serializers.CharField(write_only=True, required=False, allow_blank=True)
    delivery_frequency = serializers.CharField(write_only=True, required=False, allow_blank=True)
    buyer_registration_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    organization_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    organization_type = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        default="unclassified",
    )
    ngo_registration_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    website = serializers.URLField(write_only=True, required=False, allow_blank=True)
    focus_areas = serializers.CharField(write_only=True, required=False, allow_blank=True)
    mission = serializers.CharField(write_only=True, required=False, allow_blank=True)
    beneficiaries_served = serializers.CharField(write_only=True, required=False, allow_blank=True)
    collection_capacity = serializers.CharField(write_only=True, required=False, allow_blank=True)
    has_transport = serializers.CharField(write_only=True, required=False, allow_blank=True)
    food_types = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "password",
            "password2",
            "first_name",
            "last_name",
            "role",
            "phone",
            "google_credential",
            "province",
            "district",
            "sector",
            "cell",
            "village",
            "farm_name",
            "farm_size",
            "main_crop",
            "company_name",
            "buyer_type",
            "supply_needs",
            "monthly_volume",
            "delivery_frequency",
            "buyer_registration_number",
            "organization_name",
            "organization_type",
            "ngo_registration_number",
            "website",
            "focus_areas",
            "mission",
            "beneficiaries_served",
            "collection_capacity",
            "has_transport",
            "food_types",
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_organization_type(self, value):
        normalized = value.strip().lower()
        if normalized in dict(NGOProfile.ORGANIZATION_TYPES):
            return normalized
        if "cooperative" in normalized:
            return "cooperative"
        if "institution" in normalized or "school" in normalized or "hospital" in normalized:
            return "institution"
        if "ngo" in normalized or "non-governmental" in normalized:
            return "ngo"
        return "unclassified"

    def validate(self, data):
        if data.get("role") == "admin":
            raise serializers.ValidationError(
                {"role": "Administrator accounts must be provisioned by an administrator."}
            )
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        validated_data.pop("google_credential", None)
        location = {
            field: validated_data.pop(field, "")
            for field in ("province", "district", "sector", "cell", "village")
        }
        farmer_data = {
            field: validated_data.pop(field, "")
            for field in ("farm_name", "farm_size", "main_crop")
        }
        buyer_data = {
            field: validated_data.pop(field, "")
            for field in (
                "company_name",
                "buyer_type",
                "supply_needs",
                "monthly_volume",
                "delivery_frequency",
            )
        }
        buyer_data["registration_number"] = validated_data.pop(
            "buyer_registration_number", ""
        )
        ngo_data = {
            field: validated_data.pop(field, "")
            for field in (
                "organization_name",
                "organization_type",
                "ngo_registration_number",
                "website",
                "focus_areas",
                "mission",
                "beneficiaries_served",
                "collection_capacity",
                "has_transport",
                "food_types",
            )
        }
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.first_name = user.first_name
        profile.last_name = user.last_name
        for field, value in location.items():
            setattr(profile, field, value)
        profile.save()
        if user.role == "farmer":
            FarmerProfile.objects.create(profile=profile, **farmer_data)
        elif user.role == "buyer":
            buyer_type = buyer_data["buyer_type"]
            if buyer_type not in dict(BuyerProfile.BUYER_TYPES):
                buyer_type = "business" if buyer_data["company_name"] else "individual"
            BuyerProfile.objects.create(
                profile=profile,
                company_name=buyer_data["company_name"],
                buyer_type=buyer_type,
                supply_needs=buyer_data["supply_needs"],
                monthly_volume=buyer_data["monthly_volume"],
                delivery_frequency=buyer_data["delivery_frequency"],
                registration_number=buyer_data["registration_number"],
            )
        elif user.role == "ngo":
            NGOProfile.objects.create(
                profile=profile,
                organization_name=(
                    ngo_data["organization_name"] or user.get_full_name() or user.email
                ),
                organization_type=ngo_data["organization_type"],
                registration_number=ngo_data["ngo_registration_number"],
                website=ngo_data["website"],
                focus_areas=ngo_data["focus_areas"],
                mission=ngo_data["mission"],
                beneficiaries_served=ngo_data["beneficiaries_served"],
                collection_capacity=ngo_data["collection_capacity"],
                has_transport=ngo_data["has_transport"],
                food_types=ngo_data["food_types"],
            )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value