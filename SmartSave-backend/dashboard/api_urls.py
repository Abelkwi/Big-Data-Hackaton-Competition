from django.urls import path

from . import api_views

urlpatterns = [
    path("farmer/", api_views.FarmerDashboardView.as_view(), name="dashboard-farmer"),
    path("buyer/", api_views.BuyerDashboardView.as_view(), name="dashboard-buyer"),
    path("ngo/", api_views.NGODashboardView.as_view(), name="dashboard-ngo"),
    path("admin/", api_views.AdminDashboardView.as_view(), name="dashboard-admin"),
]