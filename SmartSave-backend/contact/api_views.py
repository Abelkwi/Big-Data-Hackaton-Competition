from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ContactMessage
from .serializers import ContactMessageSerializer

User = get_user_model()


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class ContactCreateView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = ContactMessageSerializer


class ContactListView(generics.ListAPIView):
    queryset = ContactMessage.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = ContactMessageSerializer


class MarkAsReadView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, id):
        try:
            message = ContactMessage.objects.get(id=id)
        except ContactMessage.DoesNotExist:
            return Response({"detail": "Message not found."}, status=status.HTTP_404_NOT_FOUND)
        message.is_read = True
        message.save(update_fields=["is_read"])
        return Response({"detail": "Message marked as read."})
