from django.urls import path

from .views import (
    create_listing,
    dashboard,
    marketplace_list,
    product_detail,
    toggle_wishlist,
    wishlist_list,
)


app_name = 'marketplace'

urlpatterns = [
    path('', marketplace_list, name='list'),
    path("products/<slug:slug>/", product_detail, name="product_detail"),
    path('create/', create_listing, name='create'),
    path('dashboard/', dashboard, name='dashboard'),
    path("wishlist/", wishlist_list, name="wishlist"),
    path("wishlist/toggle/<slug:slug>/", toggle_wishlist, name="toggle_wishlist"),
]
