from django.urls import path

from .views import (
    login_view,
    logout_view,
    register_view,
    farmer_store,
    toggle_follow,
)

app_name = "accounts"

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    path(
        "store/<slug:slug>/",
        farmer_store,
        name="farmer_store",
    ),

    path(
        "store/<slug:slug>/follow/",
        toggle_follow,
        name="toggle_follow",
    ),
]
