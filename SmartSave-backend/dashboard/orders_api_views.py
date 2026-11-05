from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsConfiguredAdmin
from orders.models import Order


class AdminOrdersView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def get(self, request):
        orders = Order.objects.select_related("buyer", "product").order_by("-ordered_at")
        paginator = PageNumberPagination()
        paginator.page_size = 25
        paginator.page_size_query_param = "page_size"
        paginator.max_page_size = 100
        page = paginator.paginate_queryset(orders, request, view=self)
        results = [
            {
                "id": order.pk,
                "buyer_email": order.buyer.email,
                "product_name": order.product.name,
                "quantity": str(order.quantity),
                "unit": order.product.unit,
                "total_price": str(order.total_price),
                "status": order.status,
                "ordered_at": order.ordered_at,
            }
            for order in page
        ]
        return paginator.get_paginated_response(results)
