from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Donation, DonationClaim, RecoveryListing
from .serializers import (
    DonationClaimCreateSerializer,
    DonationClaimSerializer,
    DonationCreateSerializer,
    DonationSerializer,
    RecoveryListingCreateSerializer,
    RecoveryListingSerializer,
)


class RecoveryListingListView(generics.ListAPIView):
    """Public list of recovery listings, filterable by status."""
    queryset = RecoveryListing.objects.all()
    serializer_class = RecoveryListingSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs


class RecoveryListingCreateView(generics.CreateAPIView):
    """Farmers can create a new recovery listing."""
    queryset = RecoveryListing.objects.all()
    serializer_class = RecoveryListingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(donor=self.request.user)


class RecoveryListingDetailView(generics.RetrieveAPIView):
    """Public detail view for a single recovery listing."""
    queryset = RecoveryListing.objects.all()
    serializer_class = RecoveryListingSerializer
    permission_classes = [permissions.AllowAny]


class ClaimListingView(generics.CreateAPIView):
    """Authenticated NGO/buyer can claim a recovery listing."""
    queryset = DonationClaim.objects.all()
    serializer_class = DonationClaimCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        listing = serializer.validated_data["listing"]
        if listing.status != "available":
            return Response(
                {"error": "This listing is no longer available."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_create(serializer)
        listing.status = "claimed"
        listing.save(update_fields=["status"])
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        serializer.save(claimant=self.request.user)


class DonationCreateView(generics.CreateAPIView):
    """Authenticated user can make a monetary donation."""
    queryset = Donation.objects.all()
    serializer_class = DonationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(donor=self.request.user)


class MyDonationsView(generics.ListAPIView):
    """Authenticated user can view their own donations."""
    serializer_class = DonationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Donation.objects.filter(donor=self.request.user)
