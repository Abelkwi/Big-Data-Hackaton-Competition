from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from marketplace.models import Product
from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer,
    CreateConversationSerializer,
    MessageSerializer,
    SendMessageSerializer,
)

User = get_user_model()


class ConversationListView(generics.ListAPIView):
    """List user's conversations."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationListSerializer

    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related("participants", "messages").order_by("-updated_at")


class ConversationDetailView(APIView):
    """Get conversation with all messages."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            conversation = Conversation.objects.prefetch_related(
                "messages__sender", "participants"
            ).get(id=id, participants=request.user)
        except Conversation.DoesNotExist:
            return Response(
                {"detail": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Mark messages as read
        conversation.messages.filter(is_read=False).exclude(
            sender=request.user
        ).update(is_read=True)

        serializer = ConversationDetailSerializer(
            conversation, context={"request": request}
        )
        return Response(serializer.data)


class CreateConversationView(APIView):
    """Start a new conversation."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateConversationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            recipient = User.objects.get(
                id=serializer.validated_data["recipient_id"]
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "Recipient not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if recipient == request.user:
            return Response(
                {"detail": "Cannot start a conversation with yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = None
        product_id = serializer.validated_data.get("product_id")
        if product_id:
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                pass

        # Check for existing conversation between these users about this product
        existing = Conversation.objects.filter(
            participants=request.user
        ).filter(participants=recipient)

        if product:
            existing = existing.filter(product=product)

        existing = existing.first()

        if existing:
            # Add message to existing conversation
            Message.objects.create(
                conversation=existing,
                sender=request.user,
                body=serializer.validated_data["body"],
            )
            serializer = ConversationDetailSerializer(
                existing, context={"request": request}
            )
            return Response(serializer.data)

        # Create new conversation
        conversation = Conversation.objects.create(
            subject=serializer.validated_data.get("subject", ""),
            product=product,
        )
        conversation.participants.add(request.user, recipient)

        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            body=serializer.validated_data["body"],
        )

        serializer = ConversationDetailSerializer(
            conversation, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SendMessageView(APIView):
    """Send a message in an existing conversation."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            conversation = Conversation.objects.get(
                id=id, participants=request.user
            )
        except Conversation.DoesNotExist:
            return Response(
                {"detail": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            body=serializer.validated_data["body"],
        )

        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )


class MarkAsReadView(APIView):
    """Mark a message as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            message = Message.objects.get(
                id=id,
                conversation__participants=request.user,
            )
        except Message.DoesNotExist:
            return Response(
                {"detail": "Message not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        message.is_read = True
        message.save(update_fields=["is_read"])

        return Response({"detail": "Message marked as read."})


class UnreadCountView(APIView):
    """Get total unread message count."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False,
        ).exclude(sender=request.user).count()

        return Response({"unread_count": count})