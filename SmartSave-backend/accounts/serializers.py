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
        ]
        read_only_fields = ["id"]


class NGOProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NGOProfile
        fields = [
            "id",
            "organization_name",
            "slug",
            "registration_number",
            "website",
            "mission",
            "focus_areas",
            "is_approved",
        ]
        read_only_fields = ["id", "slug", "is_approved"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

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
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value