from django.urls import path

from . import api_views

urlpatterns = [
    # Public
    path("", api_views.ProductListView.as_view(), name="marketplace-list"),
    path("featured/", api_views.FeaturedProductListView.as_view(), name="marketplace-featured"),
    path("categories/", api_views.CategoryListView.as_view(), name="marketplace-categories"),
    
    # Verification (must come before <slug:slug>/ patterns)
    path("pending-verification/", api_views.PendingVerificationListView.as_view(), name="marketplace-pending"),
    
    # Wishlist (must come before <slug:slug>/ patterns)
    path("wishlist/", api_views.WishlistView.as_view(), name="marketplace-wishlist-list"),
    
    # Farmer CRUD
    path("create/", api_views.ProductCreateView.as_view(), name="marketplace-create"),
    path("my-products/", api_views.MyProductListView.as_view(), name="marketplace-my-products"),
    path("<slug:slug>/", api_views.ProductDetailView.as_view(), name="marketplace-detail"),
    path("<slug:slug>/update/", api_views.ProductUpdateView.as_view(), name="marketplace-update"),
    path("<slug:slug>/delete/", api_views.ProductDeleteView.as_view(), name="marketplace-delete"),
    path("<slug:slug>/verify/", api_views.VerifyProductView.as_view(), name="marketplace-verify"),
    
    # Reviews & Wishlist
    path("<slug:slug>/review/", api_views.ReviewCreateView.as_view(), name="marketplace-review"),
    path("<slug:slug>/wishlist/", api_views.ToggleWishlistView.as_view(), name="marketplace-wishlist"),
]
