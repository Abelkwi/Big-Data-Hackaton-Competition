from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class User(AbstractUser):
    """Custom user model with email as primary identifier."""

    ROLE_CHOICES = [
        ("farmer", "Farmer"),
        ("buyer", "Buyer"),
        ("ngo", "NGO / Cooperative"),
        ("admin", "Administrator"),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="buyer")
    is_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.get_role_display()})"


class Profile(models.Model):
    """Extended profile information for all user types."""

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    profile_photo = models.ImageField(upload_to="profiles/", blank=True, null=True)
    bio = models.TextField(blank=True)

    # Location
    country = models.CharField(max_length=100, default="Rwanda")
    province = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, blank=True)
    village = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.user.email}"


class FarmerProfile(models.Model):
    """Farmer-specific information."""

    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name="farmer_profile"
    )
    farm_name = models.CharField(max_length=200, blank=True)
    farm_size = models.CharField(max_length=100, blank=True)  # e.g. "2 hectares"
    main_crop = models.CharField(max_length=100, blank=True)
    experience = models.PositiveIntegerField(null=True, blank=True)  # years
    certificate = models.FileField(
        upload_to="farmers/certificates/", blank=True, null=True
    )
    gps_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Store / shop
    store_name = models.CharField(max_length=150, blank=True)
    store_slug = models.SlugField(unique=True, blank=True, null=True)
    store_banner = models.ImageField(upload_to="stores/banners/", blank=True, null=True)
    store_description = models.TextField(blank=True)

    # Social links
    website = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Farmer Profile"
        verbose_name_plural = "Farmer Profiles"

    def save(self, *args, **kwargs):
        if self.store_name and not self.store_slug:
            base_slug = slugify(self.store_name)
            slug = base_slug
            counter = 1
            while FarmerProfile.objects.filter(store_slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.store_slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.farm_name or f"Farm of {self.profile.user.email}"


class BuyerProfile(models.Model):
    """Buyer-specific information."""

    BUYER_TYPES = [
        ("individual", "Individual"),
        ("business", "Business / Restaurant"),
        ("institution", "Institution / School"),
        ("wholesaler", "Wholesaler"),
    ]

    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name="buyer_profile"
    )
    company_name = models.CharField(max_length=200, blank=True)
    buyer_type = models.CharField(max_length=20, choices=BUYER_TYPES, default="individual")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Buyer Profile"
        verbose_name_plural = "Buyer Profiles"

    def __str__(self):
        return self.company_name or f"Buyer {self.profile.user.email}"


class NGOProfile(models.Model):
    """NGO / Cooperative-specific information."""

    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name="ngo_profile"
    )
    organization_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, null=True)
    registration_number = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    mission = models.TextField(blank=True)
    focus_areas = models.CharField(max_length=300, blank=True)  # comma-separated
    is_approved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "NGO Profile"
        verbose_name_plural = "NGO Profiles"

    def save(self, *args, **kwargs):
        if self.organization_name and not self.slug:
            base_slug = slugify(self.organization_name)
            slug = base_slug
            counter = 1
            while NGOProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.organization_name


class FarmerFollow(models.Model):
    """Tracks which users follow which farmers."""

    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following_farmers"
    )
    farmer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="farmer_followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "farmer")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.follower.email} follows {self.farmer.email}"