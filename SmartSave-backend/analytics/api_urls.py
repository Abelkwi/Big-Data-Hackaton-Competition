from django.urls import path
from . import api_views

urlpatterns = [
    path("overview/", api_views.AnalyticsOverviewView.as_view(), name="analytics-overview"),
    path("users/", api_views.UserAnalyticsView.as_view(), name="analytics-users"),
    path("products/", api_views.ProductAnalyticsView.as_view(), name="analytics-products"),
    path("orders/", api_views.OrderAnalyticsView.as_view(), name="analytics-orders"),
    path("top-crops/", api_views.TopCropsView.as_view(), name="analytics-top-crops"),
    path("active-districts/", api_views.ActiveDistrictsView.as_view(), name="analytics-districts"),
]