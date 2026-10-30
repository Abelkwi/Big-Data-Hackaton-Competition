"""Accounts API endpoints (farmer listings, profiles)."""

from django.urls import path

from . import api_accounts_views

urlpatterns = [
    path("farmers/", api_accounts_views.FarmerListView.as_view(), name="accounts-farmers"),
    path("farmers/<slug:slug>/", api_accounts_views.FarmerDetailView.as_view(), name="accounts-farmer-detail"),
    path("farmers/<slug:slug>/follow/", api_accounts_views.ToggleFollowView.as_view(), name="accounts-farmer-follow"),
    path("cooperatives/", api_accounts_views.CooperativeListView.as_view(), name="accounts-cooperatives"),
    path("cooperatives/<slug:slug>/", api_accounts_views.CooperativeDetailView.as_view(), name="accounts-cooperative-detail"),
]