from django.urls import path

from . import api_views

urlpatterns = [
    path("stats/", api_views.HomeStatsView.as_view(), name="home-stats"),
    path("featured-products/", api_views.FeaturedProductsView.as_view(), name="home-featured"),
]