from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import (
    User,
    Profile,
    FarmerProfile,
    BuyerProfile,
    NGOProfile,
    FarmerFollow,
)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class FarmerProfileInline(admin.StackedInline):
    model = FarmerProfile
    can_delete = False


class BuyerProfileInline(admin.StackedInline):
    model = BuyerProfile
    can_delete = False


class NGOProfileInline(admin.StackedInline):
    model = NGOProfile
    can_delete = False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "username",
        "role",
        "is_verified",
        "is_active",
        "date_joined",
    )
    list_filter = ("role", "is_verified", "is_active", "date_joined")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone")}),
        ("Permissions", {"fields": ("role", "is_verified", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2", "role"),
        }),
    )

    inlines = [ProfileInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name", "district", "sector")
    list_filter = ("country", "province", "district")
    search_fields = ("user__email", "first_name", "last_name", "phone")
    readonly_fields = ("created_at", "updated_at")


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ("farm_name", "get_user_email", "main_crop", "farm_size", "store_slug")
    search_fields = ("farm_name", "profile__user__email", "main_crop")
    readonly_fields = ("created_at", "updated_at")

    def get_user_email(self, obj):
        return obj.profile.user.email
    get_user_email.short_description = "User"


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ("get_user_email", "company_name", "buyer_type")
    search_fields = ("profile__user__email", "company_name")

    def get_user_email(self, obj):
        return obj.profile.user.email
    get_user_email.short_description = "User"


@admin.register(NGOProfile)
class NGOProfileAdmin(admin.ModelAdmin):
    list_display = ("organization_name", "get_user_email", "is_approved", "created_at")
    list_filter = ("is_approved",)
    search_fields = ("organization_name", "profile__user__email")

    def get_user_email(self, obj):
        return obj.profile.user.email
    get_user_email.short_description = "User"


@admin.register(FarmerFollow)
class FarmerFollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "farmer", "created_at")
    search_fields = ("follower__email", "farmer__email")
    readonly_fields = ("created_at",)