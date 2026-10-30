from django.conf import settings
from django.db import models
from django.db.models import Avg
from django.utils.text import slugify


User = settings.AUTH_USER_MODEL


class Category(models.Model):
    """Product category with icon and metadata."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class or emoji")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["display_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Agricultural product listing from a farmer."""

    STATUS_CHOICES = [
        ("available", "Available"),
        ("out_of_stock", "Out of Stock"),
        ("reserved", "Reserved"),
        ("sold", "Sold"),
    ]

    VERIFICATION_CHOICES = [
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]

    farmer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="products"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    variety = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    main_image = models.ImageField(
        upload_to="products/main/", blank=True, null=True
    )

    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default="kg")
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2)

    province = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, blank=True)

    harvest_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    organic = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20, choices=VERIFICATION_CHOICES, default="pending"
    )
    availability_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="available"
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def average_rating(self):
        avg = self.reviews.filter(is_approved=True).aggregate(Avg("rating"))
        return round(avg["rating__avg"] or 0, 1)

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "availability_status"]),
            models.Index(fields=["farmer", "-created_at"]),
            models.Index(fields=["verification_status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    """Gallery images for a product."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/gallery/")
    caption = models.CharField(max_length=150, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "uploaded_at"]

    def __str__(self):
        return f"{self.product.name} Image {self.id}"


class Review(models.Model):
    """Product review from a buyer."""

    RATING_CHOICES = [
        (1, "★☆☆☆☆"),
        (2, "★★☆☆☆"),
        (3, "★★★☆☆"),
        (4, "★★★★☆"),
        (5, "★★★★★"),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "buyer"],
                name="one_review_per_buyer_per_product",
            )
        ]

    def __str__(self):
        return f"{self.product.name} - {self.rating}★ by {self.buyer.email}"


class Wishlist(models.Model):
    """User's saved/favorite products."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="wishlist_items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} ♥ {self.product.name}"