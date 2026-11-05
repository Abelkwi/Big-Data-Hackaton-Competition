from rest_framework import serializers

from accounts.models import User

from .models import Announcement, AuditEvent, ModerationReport


class AdminUserListSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    province = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    sector = serializers.SerializerMethodField()
    organization_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "is_verified",
            "status",
            "date_joined",
            "last_login",
            "province",
            "district",
            "sector",
            "organization_type",
        ]

    def get_status(self, user):
        if not user.is_active:
            return "suspended"
        if not user.is_verified:
            return "pending"
        return "active"

    def get_province(self, user):
        profile = getattr(user, "profile", None)
        return profile.province if profile else ""

    def get_district(self, user):
        profile = getattr(user, "profile", None)
        return profile.district if profile else ""

    def get_sector(self, user):
        profile = getattr(user, "profile", None)
        return profile.sector if profile else ""

    def get_organization_type(self, user):
        profile = getattr(user, "profile", None)
        organization = getattr(profile, "ngo_profile", None) if profile else None
        return organization.organization_type if organization else None


class AdminUserDetailSerializer(AdminUserListSerializer):
    phone = serializers.CharField(read_only=True)
    profile = serializers.SerializerMethodField()
    farmer_profile = serializers.SerializerMethodField()
    buyer_profile = serializers.SerializerMethodField()
    ngo_profile = serializers.SerializerMethodField()

    class Meta(AdminUserListSerializer.Meta):
        fields = AdminUserListSerializer.Meta.fields + [
            "phone",
            "profile",
            "farmer_profile",
            "buyer_profile",
            "ngo_profile",
        ]

    def get_profile(self, user):
        profile = getattr(user, "profile", None)
        if not profile:
            return None
        return {
            "bio": profile.bio,
            "country": profile.country,
            "province": profile.province,
            "district": profile.district,
            "sector": profile.sector,
            "village": profile.village,
        }

    def get_farmer_profile(self, user):
        profile = getattr(user, "profile", None)
        farmer = getattr(profile, "farmer_profile", None) if profile else None
        if not farmer:
            return None
        return {
            "farm_name": farmer.farm_name,
            "main_crop": farmer.main_crop,
            "farm_size": farmer.farm_size,
        }

    def get_buyer_profile(self, user):
        profile = getattr(user, "profile", None)
        buyer = getattr(profile, "buyer_profile", None) if profile else None
        if not buyer:
            return None
        return {"company_name": buyer.company_name, "buyer_type": buyer.buyer_type}

    def get_ngo_profile(self, user):
        profile = getattr(user, "profile", None)
        ngo = getattr(profile, "ngo_profile", None) if profile else None
        if not ngo:
            return None
        return {
            "organization_name": ngo.organization_name,
            "registration_number": ngo.registration_number,
            "website": ngo.website,
            "focus_areas": ngo.focus_areas,
            "is_approved": ngo.is_approved,
            "organization_type": ngo.organization_type,
        }


class AuditEventSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "event_type",
            "user_email",
            "user_identifier",
            "user_role",
            "description",
            "metadata",
            "created_at",
        ]

    def get_user_email(self, event):
        return event.user.email if event.user_id else event.user_identifier or None


class AnnouncementSerializer(serializers.ModelSerializer):
    is_published = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = Announcement
        fields = [
            "id",
            "title",
            "body",
            "category",
            "audience",
            "visibility",
            "is_pinned",
            "status",
            "is_published",
            "publish_at",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        is_published = validated_data.pop("is_published", None)
        if is_published is not None:
            validated_data["status"] = "published" if is_published else "draft"
        return super().create(validated_data)

    def update(self, instance, validated_data):
        is_published = validated_data.pop("is_published", None)
        if is_published is not None and "status" not in validated_data:
            validated_data["status"] = "published" if is_published else "draft"
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["is_published"] = instance.status == "published"
        return data

    def validate(self, attrs):
        publish_at = attrs.get("publish_at", getattr(self.instance, "publish_at", None))
        expires_at = attrs.get("expires_at", getattr(self.instance, "expires_at", None))
        if publish_at and expires_at and expires_at <= publish_at:
            raise serializers.ValidationError(
                {"expires_at": "The expiration time must be after the publish time."}
            )
        return attrs


class ModerationReportSerializer(serializers.ModelSerializer):
    reporter_email = serializers.SerializerMethodField()

    class Meta:
        model = ModerationReport
        fields = [
            "id",
            "reporter_email",
            "target_type",
            "target_id",
            "reason",
            "status",
            "resolution",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_reporter_email(self, report):
        return report.reporter.email if report.reporter_id else None
