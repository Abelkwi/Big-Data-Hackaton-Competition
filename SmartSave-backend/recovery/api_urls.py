from django.urls import path

from . import api_views

urlpatterns = [
    path("", api_views.RecoveryListingListView.as_view(), name="recovery-list"),
    path("create/", api_views.RecoveryListingCreateView.as_view(), name="recovery-create"),
    path("<int:pk>/", api_views.RecoveryListingDetailView.as_view(), name="recovery-detail"),
    path("<int:pk>/claim/", api_views.ClaimListingView.as_view(), name="recovery-claim"),
    path("donations/create/", api_views.DonationCreateView.as_view(), name="donation-create"),
    path("donations/", api_views.MyDonationsView.as_view(), name="my-donations"),
]
