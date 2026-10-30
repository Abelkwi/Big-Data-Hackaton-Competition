from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import F

from .forms import ProductForm, ReviewForm
from .models import (
    Product,
    ProductImage,
    Review,
    Wishlist,
)

User = get_user_model()


def marketplace_list(request):
    products = (
        Product.objects
        .select_related("farmer", "farmer__profile")
        .filter(
            availability_status="available",
            verification_status="verified",
        )
        .order_by("-created_at")
    )

    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()
    district = request.GET.get("district", "").strip()

    if search:
        products = products.filter(
            name__icontains=search
        )

    if category:
        products = products.filter(
        category=category
        )

    if district:
        products = products.filter(
        district__icontains=district
        )

    return render(
        request,
        "marketplace/list.html",
        {
            "products": products,
            "categories": Product.CATEGORY_CHOICES,
            "selected_category": category,
            "selected_district": district,
            "search_query": search,
        },
    )

@login_required
def create_listing(request):

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            product = form.save(commit=False)
            product.farmer = request.user
            product.save()

            gallery_images = request.FILES.getlist("gallery_images")

            for index, image in enumerate(gallery_images):

                ProductImage.objects.create(
                    product=product,
                    image=image,
                    display_order=index
                )

            messages.success(
                request,
                "Product listed successfully."
            )

            return redirect("marketplace:dashboard")

    else:
        form = ProductForm()

    return render(
        request,
        "marketplace/create_listing.html",
        {
            "form": form,
        },
    )


@login_required
def dashboard(request):

    my_products = (
        Product.objects
        .filter(farmer=request.user)
        .order_by("-created_at")
    )

    return render(
        request,
        "marketplace/dashboard.html",
        {
            "products": my_products,
        },
    )

def product_detail(request, slug):

    product = get_object_or_404(
        Product.objects.select_related(
            "farmer",
            "farmer__profile"
        ).prefetch_related(
            "images",
            "reviews",
        ),
        slug=slug,
        is_active=True,
    )

    Product.objects.filter(
        pk=product.pk
    ).update(
        views=F("views") + 1
    )

    product.refresh_from_db()

    reviews = (
        product.reviews
        .filter(is_approved=True)
        .select_related("buyer")
        .order_by("-created_at")
    )

    if request.method == "POST":

        if not request.user.is_authenticated:

            messages.error(
                request,
                "Please login first."
            )

            return redirect("accounts:login")

        form = ReviewForm(request.POST)

        if form.is_valid():

            review, created = Review.objects.update_or_create(
                product=product,
                buyer=request.user,
                defaults={
                    "rating": form.cleaned_data["rating"],
                    "comment": form.cleaned_data["comment"],
                }
            )

            if created:
                messages.success(
                    request,
                    "Review submitted successfully."
                )
            else:
                messages.success(
                    request,
                    "Review updated successfully."
                )

            return redirect(
                "marketplace:product_detail",
                slug=product.slug
            )

    else:
        form = ReviewForm()

    gallery_images = product.images.all()

    related_products = (
        Product.objects.filter(
            category=product.category,
            is_active=True,
            availability_status="available",
        )
        .exclude(pk=product.pk)
        .order_by("-created_at")[:8]
    )

    recent_products = (
        Product.objects.filter(
            is_active=True,
            availability_status="available",
        )
        .exclude(pk=product.pk)
        .order_by("-created_at")[:8]
    )

    wishlist = False

    if request.user.is_authenticated:

        wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product,
        ).exists()

    context = {
        "product": product,
        "gallery_images": gallery_images,
        "farmer": product.farmer,
        "related_products": related_products,
        "recent_products": recent_products,
        "reviews": reviews,
        "average_rating": product.average_rating,
        "review_count": product.review_count,
        "review_form": form,
        "wishlist": wishlist,
    }

    return render(
        request,
        "marketplace/product_detail.html",
        context,
    )

@login_required
def toggle_wishlist(request, slug):

    product = get_object_or_404(
        Product,
        slug=slug,
        is_active=True,
    )

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product,
    ).first()

    if wishlist_item:

        wishlist_item.delete()

        messages.success(
            request,
            "Product removed from wishlist."
        )

    else:

        Wishlist.objects.create(
            user=request.user,
            product=product,
        )

        messages.success(
            request,
            "Product added to wishlist."
        )

    return redirect(
        "marketplace:product_detail",
        slug=product.slug,
    )


@login_required
def wishlist_list(request):

    wishlist_items = (
        Wishlist.objects
        .filter(user=request.user)
        .select_related(
            "product",
            "product__farmer",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "marketplace/wishlist.html",
        {
            "wishlist_items": wishlist_items,
        },
    )