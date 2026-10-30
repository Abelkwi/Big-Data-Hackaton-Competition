from django.urls import path

from . import api_views

urlpatterns = [
    # Cart
    path("cart/", api_views.CartView.as_view(), name="cart"),
    path("cart/add/", api_views.AddToCartView.as_view(), name="cart-add"),
    path("cart/item/<int:item_id>/", api_views.UpdateCartItemView.as_view(), name="cart-item-update"),
    path("cart/item/<int:item_id>/remove/", api_views.RemoveFromCartView.as_view(), name="cart-item-remove"),
    path("cart/clear/", api_views.ClearCartView.as_view(), name="cart-clear"),
    
    # Checkout
    path("checkout/", api_views.CheckoutView.as_view(), name="checkout"),
    
    # Orders
    path("", api_views.MyOrderListView.as_view(), name="order-list"),
    path("<int:id>/", api_views.OrderDetailView.as_view(), name="order-detail"),
    path("<int:id>/cancel/", api_views.CancelOrderView.as_view(), name="order-cancel"),
    path("<int:id>/status/", api_views.UpdateOrderStatusView.as_view(), name="order-status"),
    path("farmer/", api_views.FarmerOrderListView.as_view(), name="order-farmer-list"),
]