from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile, FarmerProfile, BuyerProfile, NGOProfile
from .serializers import (
    UserSerializer,
    ProfileSerializer,
    FarmerProfileSerializer,
    BuyerProfileSerializer,
    NGOProfileSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new user with any role."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class FarmerRegisterView(generics.CreateAPIView):
    """Register a new farmer."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save(role="farmer")
        Profile.objects.get_or_create(user=user)
        FarmerProfile.objects.get_or_create(profile=user.profile)


class BuyerRegisterView(generics.CreateAPIView):
    """Register a new buyer."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save(role="buyer")
        Profile.objects.get_or_create(user=user)
        BuyerProfile.objects.get_or_create(profile=user.profile)


class NGORegisterView(generics.CreateAPIView):
    """Register a new NGO/Cooperative."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save(role="ngo")
        Profile.objects.get_or_create(user=user)
        NGOProfile.objects.get_or_create(profile=user.profile)


class ProfileView(APIView):
    """Get current user's profile."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data

        # Add role-specific profile data
        if hasattr(user, "profile"):
            data["profile"] = ProfileSerializer(user.profile).data

        if user.role == "farmer" and hasattr(user.profile, "farmer_profile"):
            data["farmer_profile"] = FarmerProfileSerializer(user.profile.farmer_profile).data

        if user.role == "buyer" and hasattr(user.profile, "buyer_profile"):
            data["buyer_profile"] = BuyerProfileSerializer(user.profile.buyer_profile).data

        if user.role == "ngo" and hasattr(user.profile, "ngo_profile"):
            data["ngo_profile"] = NGOProfileSerializer(user.profile.ngo_profile).data

        return Response(data)


class ProfileUpdateView(generics.UpdateAPIView):
    """Update current user's profile."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile


class ChangePasswordView(APIView):
    """Change current user's password."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data["new_password"])
            request.user.save()
            return Response({"detail": "Password updated successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)