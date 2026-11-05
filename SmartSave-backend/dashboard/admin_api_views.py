import csv
from datetime import timedelta
from io import StringIO
from itertools import islice
from time import perf_counter

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.db.models import Count, F, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import NGOProfile, Profile
from accounts.permissions import IsConfiguredAdmin
from blog.models import BlogComment, BlogPost
from marketplace.models import Product, Review
from orders.models import Order, OrderItem
from recovery.models import DonationClaim, RecoveryListing

from .admin_serializers import (
    AdminUserDetailSerializer,
    AdminUserListSerializer,
    AnnouncementSerializer,
    AuditEventSerializer,
    ModerationReportSerializer,
)
from .audit import record_event
from .models import Announcement, AuditEvent, ModerationReport
from notifications.models import Notification


User = get_user_model()


def _event_queryset():
    return AuditEvent.objects.select_related("user").all()


def _csv_safe(value):
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{value}"
    return value


def _announcement_recipients(announcement):
    recipients = User.objects.filter(is_active=True, is_verified=True)
    if announcement.audience == "farmer":
        return recipients.filter(role="farmer")
    if announcement.audience == "buyer":
        return recipients.filter(role="buyer")
    if announcement.audience == "ngo":
        return recipients.filter(role="ngo")
    if announcement.audience == "cooperative":
        return recipients.filter(
            role="ngo",
            profile__ngo_profile__organization_type="cooperative",
        )
    if announcement.audience == "institution":
        return recipients.filter(
            Q(
                role="ngo",
                profile__ngo_profile__organization_type="institution",
            )
            | Q(
                role="buyer",
                profile__buyer_profile__buyer_type="institution",
            )
        ).distinct()
    return recipients


def _dispatch_announcement_notifications(announcement):
    now = timezone.now()
    if (
        announcement.status != "published"
        or (announcement.publish_at and announcement.publish_at > now)
        or announcement.visibility not in {"dashboard", "both"}
        or announcement.notifications_sent_at
    ):
        return
    with transaction.atomic():
        announcement = Announcement.objects.select_for_update().get(pk=announcement.pk)
        if announcement.notifications_sent_at:
            return
        recipient_iterator = _announcement_recipients(announcement).iterator(
            chunk_size=500
        )
        while recipients := list(islice(recipient_iterator, 500)):
            Notification.objects.bulk_create(
                [
                    Notification(
                        recipient=user,
                        notification_type="announcement",
                        title=announcement.title,
                        body=announcement.body,
                        link="/",
                    )
                    for user in recipients
                ],
                batch_size=500,
            )
        announcement.notifications_sent_at = now
        announcement.save(update_fields=["notifications_sent_at", "updated_at"])


class AdminPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class AdminUsersView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def _filtered_users(self, request):
        users = User.objects.select_related(
            "profile", "profile__ngo_profile", "profile__buyer_profile"
        )
        search = request.query_params.get("search", "").strip()
        role = request.query_params.get("role", "").strip()
        account_status = request.query_params.get("status", "").strip()
        province = request.query_params.get("province", "").strip()
        district = request.query_params.get("district", "").strip()
        sector = request.query_params.get("sector", "").strip()
        if search:
            users = users.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(username__icontains=search)
                | Q(profile__ngo_profile__organization_name__icontains=search)
            )
        if role in {"farmer", "buyer", "ngo", "admin"}:
            users = users.filter(role=role)
        if account_status == "suspended":
            users = users.filter(is_active=False)
        elif account_status == "pending":
            users = users.filter(is_active=True, is_verified=False)
        elif account_status == "active":
            users = users.filter(is_active=True, is_verified=True)
        if province:
            users = users.filter(profile__province__iexact=province)
        if district:
            users = users.filter(profile__district__iexact=district)
        if sector:
            users = users.filter(profile__sector__iexact=sector)
        return users.distinct()

    def get(self, request):
        users = self._filtered_users(request)
        ordering = request.query_params.get("ordering", "-date_joined")
        if ordering not in {"date_joined", "-date_joined", "email", "-email"}:
            ordering = "-date_joined"
        users = users.order_by(ordering)
        if request.query_params.get("export") == "csv":
            output = StringIO()
            writer = csv.writer(output)
            fields = [
                "id", "email", "first_name", "last_name", "role",
                "organization_type", "province", "district", "sector",
                "status", "is_verified", "date_joined", "last_login",
            ]
            writer.writerow(fields)
            for user in users.iterator(chunk_size=500):
                row = AdminUserListSerializer(user).data
                writer.writerow([_csv_safe(row[field]) for field in fields])
            response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = 'attachment; filename="smartsave-users.csv"'
            return response
        paginator = AdminPagination()
        page = paginator.paginate_queryset(users, request, view=self)
        return paginator.get_paginated_response(AdminUserListSerializer(page, many=True).data)


class AdminUserDetailView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        return Response(AdminUserDetailSerializer(user).data)

    def patch(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        allowed_user_fields = {"first_name": 150, "last_name": 150, "phone": 20}
        allowed_profile_fields = {"province": 100, "district": 100, "sector": 100}
        updates = request.data
        if not isinstance(updates, dict) or not updates:
            return Response(
                {"detail": "Provide at least one permitted profile field."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        allowed_fields = (
            set(allowed_user_fields)
            | set(allowed_profile_fields)
            | {"organization_type"}
        )
        if set(updates) - allowed_fields:
            return Response(
                {"detail": "One or more fields cannot be edited from this console."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for field, value in updates.items():
            limit = (
                allowed_user_fields.get(field)
                or allowed_profile_fields.get(field)
                or 20
            )
            if not isinstance(value, str) or len(value) > limit:
                return Response(
                    {field: f"Enter text of no more than {limit} characters."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if "organization_type" in updates:
            valid_types = {choice[0] for choice in NGOProfile.ORGANIZATION_TYPES}
            if updates["organization_type"] not in valid_types:
                return Response(
                    {"organization_type": "Choose a valid organization classification."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if user.role != "ngo":
                return Response(
                    {"organization_type": "Only organization accounts have this field."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            user_fields = [field for field in updates if field in allowed_user_fields]
            for field in user_fields:
                setattr(user, field, updates[field].strip())
            if user_fields:
                user.save(update_fields=user_fields)
            profile_fields = [
                field for field in updates if field in allowed_profile_fields
            ]
            if profile_fields:
                profile, _ = Profile.objects.get_or_create(user=user)
                for field in profile_fields:
                    setattr(profile, field, updates[field].strip())
                profile.save(update_fields=profile_fields + ["updated_at"])
            if "organization_type" in updates:
                organization = get_object_or_404(NGOProfile, profile__user=user)
                organization.organization_type = updates["organization_type"]
                organization.save(update_fields=["organization_type", "updated_at"])
            record_event(
                "admin_action",
                request=request,
                user=user,
                actor=request.user,
                description=f"Updated account profile fields: {', '.join(sorted(updates))}",
                metadata={"fields": sorted(updates)},
            )
        user.refresh_from_db()
        return Response(AdminUserDetailSerializer(user).data)


class AdminUserVerificationView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        verified = request.data.get("verified")
        reason = request.data.get("reason", "")
        if not isinstance(verified, bool):
            return Response(
                {"detail": "verified must be true or false."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            return Response(
                {"detail": "A verification note of 1–500 characters is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_staff or user.pk == request.user.pk:
            return Response(
                {"detail": "Administrator accounts cannot be verified here."},
                status=status.HTTP_403_FORBIDDEN,
            )
        user.is_verified = verified
        user.save(update_fields=["is_verified"])
        if user.role == "ngo":
            NGOProfile.objects.filter(profile__user=user).update(
                is_approved=verified and user.is_active
            )
        record_event(
            "admin_action",
            request=request,
            user=user,
            actor=request.user,
            description=f"Account verification {'approved' if verified else 'revoked'}: {reason.strip()}",
            metadata={"verified": verified},
        )
        return Response(AdminUserDetailSerializer(user).data)


class AdminUserActivityView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        events = _event_queryset().filter(
            Q(user=user) | Q(user__isnull=True, user_identifier__iexact=user.email)
        )[:100]
        return Response(AuditEventSerializer(events, many=True).data)


class AdminUserStatusView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        new_status = request.data.get("status")
        reason = request.data.get("reason", "")
        if new_status not in {"active", "suspended"}:
            return Response(
                {"detail": "Status must be active or suspended."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            return Response(
                {"detail": "A reason of 1–500 characters is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_staff or user.pk == request.user.pk:
            return Response(
                {"detail": "Administrator accounts cannot be changed here."},
                status=status.HTTP_403_FORBIDDEN,
            )
        user.is_active = new_status == "active"
        user.save(update_fields=["is_active"])
        if user.role == "ngo" and hasattr(user, "profile"):
            NGOProfile.objects.filter(profile=user.profile).update(
                is_approved=user.is_active and user.is_verified
            )
        AuditEvent.objects.create(
            event_type="account_suspension",
            user=user,
            actor=request.user,
            user_identifier=user.email,
            user_role=user.role,
            description=f"Account {new_status}: {reason.strip()}",
            metadata={"status": new_status},
        )
        return Response(AdminUserListSerializer(user).data)


class AdminActivityView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def get(self, request):
        events = _event_queryset()
        event_type = request.query_params.get("event_type", "").strip()
        search = request.query_params.get("search", "").strip()
        if event_type:
            events = events.filter(event_type=event_type)
        if search:
            events = events.filter(
                Q(user__email__icontains=search)
                | Q(user_identifier__icontains=search)
                | Q(description__icontains=search)
            )
        paginator = AdminPagination()
        paginator.page_size = 100
        page = paginator.paginate_queryset(events, request, view=self)
        return paginator.get_paginated_response(AuditEventSerializer(page, many=True).data)


class AdminOverviewView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def get(self, request):
        now = timezone.now()
        today = timezone.localdate()
        start_day = today - timedelta(days=6)
        start_month = (today.replace(day=1) - timedelta(days=365)).replace(day=1)
        recent_start = now - timedelta(days=30)
        events = _event_queryset()

        roles = dict(User.objects.values_list("role").annotate(total=Count("id")))
        registrations_today = User.objects.filter(date_joined__date=today).count()
        registrations_week = User.objects.filter(
            date_joined__date__gte=today - timedelta(days=today.weekday())
        ).count()
        registrations_month = User.objects.filter(
            date_joined__year=today.year, date_joined__month=today.month
        ).count()
        active_days = "30"
        active_users = events.filter(
            event_type="login_success",
            created_at__gte=now - timedelta(days=int(active_days)),
            user_id__isnull=False,
        ).values("user_id").distinct().count()
        active_login_events = events.filter(
            event_type="login_success",
            created_at__gte=recent_start,
            user_id__isnull=False,
        )
        login_counts = active_login_events.values("user_id").annotate(
            login_count=Count("id")
        )
        new_active_users = active_login_events.filter(
            user__date_joined__gte=recent_start
        ).values("user_id").distinct().count()
        daily_active_users = events.filter(
            event_type="login_success",
            created_at__date=today,
            user_id__isnull=False,
        ).values("user_id").distinct().count()
        weekly_active_users = events.filter(
            event_type="login_success",
            created_at__gte=now - timedelta(days=7),
            user_id__isnull=False,
        ).values("user_id").distinct().count()
        login_success = events.filter(
            event_type="login_success", created_at__gte=recent_start
        )
        login_failed = events.filter(
            event_type="login_failed", created_at__gte=recent_start
        )

        registrations = list(
            User.objects.filter(date_joined__date__gte=start_month)
            .annotate(period=TruncMonth("date_joined"))
            .values("period")
            .annotate(value=Count("id"))
            .order_by("period")
        )
        registration_series = [
            {"label": row["period"].strftime("%b"), "value": row["value"]}
            for row in registrations
        ]

        daily_users = list(
            User.objects.filter(date_joined__date__gte=start_day)
            .annotate(day=TruncDate("date_joined"))
            .values("day")
            .annotate(value=Count("id"))
            .order_by("day")
        )
        registration_days = {
            row["day"]: row["value"] for row in daily_users
        }
        recent_registrations = [
            {
                "label": (start_day + timedelta(days=offset)).strftime("%a"),
                "value": registration_days.get(start_day + timedelta(days=offset), 0),
            }
            for offset in range(7)
        ]
        daily_start = today - timedelta(days=29)
        daily_registration_rows = list(
            User.objects.filter(date_joined__date__gte=daily_start)
            .annotate(day=TruncDate("date_joined"))
            .values("day")
            .annotate(value=Count("id"))
        )
        registrations_by_day = {row["day"]: row["value"] for row in daily_registration_rows}
        last_30_days = [
            {
                "label": (daily_start + timedelta(days=offset)).strftime("%d"),
                "value": registrations_by_day.get(daily_start + timedelta(days=offset), 0),
            }
            for offset in range(30)
        ]

        activity_rows = list(
            events.filter(created_at__date__gte=start_day)
            .values("created_at__date", "event_type")
            .annotate(value=Count("id"))
        )
        activity_by_day = {}
        for row in activity_rows:
            day = row["created_at__date"]
            values = activity_by_day.setdefault(day, {"logins": 0, "other": 0})
            values["logins" if row["event_type"] == "login_success" else "other"] += row["value"]
        activity_series = [
            {
                "label": (start_day + timedelta(days=offset)).strftime("%a"),
                "value": activity_by_day.get(start_day + timedelta(days=offset), {}).get("logins", 0),
                "other": activity_by_day.get(start_day + timedelta(days=offset), {}).get("other", 0),
            }
            for offset in range(7)
        ]

        monthly_start = (today.replace(day=1) - timedelta(days=365)).replace(day=1)
        monthly_rows = list(
            events.filter(created_at__date__gte=monthly_start)
            .values("created_at__year", "created_at__month", "event_type")
            .annotate(value=Count("id"))
        )
        monthly_activity = {}
        for row in monthly_rows:
            month_key = (row["created_at__year"], row["created_at__month"])
            values = monthly_activity.setdefault(month_key, {"logins": 0, "other": 0})
            values["logins" if row["event_type"] == "login_success" else "other"] += row["value"]
        month_periods = []
        cursor_date = monthly_start
        for _ in range(12):
            month_periods.append((cursor_date.year, cursor_date.month, cursor_date.strftime("%b")))
            cursor_date = (cursor_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        monthly_activity_series = [
            {
                "label": label,
                "value": monthly_activity.get((year, month), {}).get("logins", 0),
                "other": monthly_activity.get((year, month), {}).get("other", 0),
            }
            for year, month, label in month_periods
        ]

        all_registrations = list(
            User.objects.annotate(period=TruncMonth("date_joined"))
            .values("period")
            .annotate(value=Count("id"))
            .order_by("period")
        )
        growth = []
        total = 0
        for row in all_registrations[-12:]:
            total += row["value"]
            growth.append({"label": row["period"].strftime("%b"), "value": total})

        pending_products = Product.objects.filter(verification_status="pending")
        draft_posts = BlogPost.objects.filter(is_published=False)
        pending_comments = BlogComment.objects.filter(is_approved=False)
        pending_items = [
            {
                "id": item.pk,
                "item_type": "product",
                "type": "Product verification",
                "title": item.name,
                "status": item.verification_status,
                "created_at": item.created_at,
            }
            for item in pending_products.order_by("-created_at")[:5]
        ]
        pending_items += [
            {
                "id": item.pk,
                "item_type": "post",
                "type": "Blog post review",
                "title": item.title,
                "status": "draft",
                "created_at": item.created_at,
            }
            for item in draft_posts.order_by("-created_at")[:5]
        ]
        pending_items += [
            {
                "id": item.pk,
                "item_type": "report",
                "type": "User report",
                "title": item.reason[:100],
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in ModerationReport.objects.filter(status="open").order_by("-created_at")[:5]
        ]

        database_status = "healthy"
        started = perf_counter()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        database_latency_ms = round((perf_counter() - started) * 1000, 1)

        organization_profiles = NGOProfile.objects.select_related("profile__user")
        cooperative_count = organization_profiles.filter(
            organization_type="cooperative"
        ).count()
        institutional_partner_count = organization_profiles.filter(
            organization_type="institution"
        ).count() + User.objects.filter(
            role="buyer", profile__buyer_profile__buyer_type="institution"
        ).count()
        farmers_count = roles.get("farmer", 0)
        buyers_count = roles.get("buyer", 0)
        published_posts = BlogPost.objects.filter(is_published=True).count()
        published_listings = Product.objects.filter(
            is_active=True,
            verification_status="verified",
        ).count()
        location_field = request.query_params.get("geography_level", "province")
        location_fields = {
            "province": "province",
            "district": "district",
            "sector": "sector",
        }
        if location_field not in location_fields:
            location_field = "province"
        location_lookup = f"profile__{location_fields[location_field]}"
        geography = list(
            User.objects.filter(**{f"{location_lookup}__gt": ""})
            .values(location=F(location_lookup))
            .annotate(users=Count("id", distinct=True))
            .order_by("-users", "location")[:10]
        )

        selected_period = request.query_params.get("period", "12")
        if selected_period not in {"7", "30", "6", "12"}:
            selected_period = "12"
        if selected_period in {"7", "30"}:
            days = int(selected_period)
            growth_start = today - timedelta(days=days - 1)
            growth_rows = {
                row["period"]: row["value"]
                for row in User.objects.filter(date_joined__date__gte=growth_start)
                .annotate(period=TruncDate("date_joined"))
                .values("period")
                .annotate(value=Count("id"))
            }
            registration_trend = [
                {
                    "label": (growth_start + timedelta(days=offset)).strftime("%a" if days == 7 else "%d %b"),
                    "value": growth_rows.get(growth_start + timedelta(days=offset), 0),
                }
                for offset in range(days)
            ]
        else:
            months = int(selected_period)
            growth_start = today.replace(day=1)
            for _ in range(months - 1):
                growth_start = (growth_start.replace(day=1) - timedelta(days=1)).replace(day=1)
            growth_rows = {
                (row["period"].year, row["period"].month): row["value"]
                for row in User.objects.filter(date_joined__date__gte=growth_start)
                .annotate(period=TruncMonth("date_joined"))
                .values("period")
                .annotate(value=Count("id"))
            }
            registration_trend = []
            cursor_date = growth_start
            for _ in range(months):
                registration_trend.append(
                    {
                        "label": cursor_date.strftime("%b %y"),
                        "value": growth_rows.get((cursor_date.year, cursor_date.month), 0),
                    }
                )
                cursor_date = (cursor_date.replace(day=28) + timedelta(days=4)).replace(day=1)

        summary = {
            "total_users": User.objects.count(),
            "active_users": active_users,
            "active_accounts": User.objects.filter(
                is_active=True, is_verified=True
            ).count(),
            "active_users_30d": active_users,
            "active_users_period": active_users,
            "daily_active_users": daily_active_users,
            "weekly_active_users": weekly_active_users,
            "monthly_active_users": active_users,
            "returning_users_30d": login_counts.filter(login_count__gt=1).count(),
            "new_active_users_30d": new_active_users,
            "returning_active_users_30d": max(0, active_users - new_active_users),
            "registrations_today": registrations_today,
            "registrations_week": registrations_week,
            "registrations_month": registrations_month,
            "successful_logins_30d": login_success.count(),
            "failed_logins_30d": login_failed.count(),
            "total_logins_30d": login_success.count(),
            "published_content": published_posts + published_listings,
            "published_posts": published_posts,
            "published_listings": published_listings,
            "pending_review": pending_products.count() + draft_posts.count() + pending_comments.count(),
            "pending_products": pending_products.count(),
            "pending_posts": draft_posts.count() + pending_comments.count(),
            "open_reports": ModerationReport.objects.filter(status="open").count(),
            "suspended_users": User.objects.filter(is_active=False).count(),
            "farmers": farmers_count,
            "cooperatives": cooperative_count,
            "buyers": buyers_count,
            "institutional_partners": institutional_partner_count,
            "unclassified_organizations": organization_profiles.filter(
                organization_type="unclassified"
            ).count(),
            "products": published_listings,
            "orders": Order.objects.count(),
            "active_recoveries": RecoveryListing.objects.filter(status="available").count(),
            "users_by_role": roles,
            "api_status": "Operational",
            "api_latency_ms": database_latency_ms,
            "server_errors_24h": None,
            "storage_status": "Not configured",
        }
        recent_events = events.order_by("-created_at")[:8]
        return Response(
            {
                "summary": summary,
                "analytics": {
                    "registrations": registration_trend,
                    "activity": [
                        {**row, "value": row["value"]}
                        for row in activity_series
                    ],
                    "activity_monthly": monthly_activity_series,
                    "growth": growth,
                    "geography": geography,
                    "geography_level": location_field,
                    "engagement": {
                        "daily_active_users": daily_active_users,
                        "weekly_active_users": weekly_active_users,
                        "monthly_active_users": active_users,
                        "new_active_users": new_active_users,
                        "returning_active_users": max(0, active_users - new_active_users),
                        "returning_users": login_counts.filter(login_count__gt=1).count(),
                    },
                },
                "recent_events": AuditEventSerializer(recent_events, many=True).data,
                "pending_items": pending_items[:10],
                "health": {
                    "checked_at": now,
                    "api_status": "Operational",
                    "api_latency_ms": database_latency_ms,
                    "server_errors_24h": None,
                    "storage_status": "Not configured",
                    "services": {
                        "api": "healthy",
                        "database": database_status,
                        "storage": "not_configured",
                        "backups": "not_configured",
                    },
                },
            }
        )


class AdminHealthView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def get(self, request):
        now = timezone.now()
        started = perf_counter()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        latency = round((perf_counter() - started) * 1000, 1)
        failed_logins = _event_queryset().filter(
            event_type="login_failed",
            created_at__gte=now - timedelta(hours=24),
        )
        recent_security = failed_logins[:10]
        return Response(
            {
                "checked_at": now,
                "api_status": "Operational",
                "api_latency_ms": latency,
                "server_errors_24h": None,
                "storage_status": "Not configured",
                "security": {
                    "failed_login_attempts_24h": failed_logins.count(),
                    "recent_failed_logins": AuditEventSerializer(
                        recent_security, many=True
                    ).data,
                },
                "services": {
                    "api": "healthy",
                    "database": "healthy",
                    "website": "not_configured",
                    "storage": "not_configured",
                    "backups": "not_configured",
                },
            }
        )


class AdminInsightsReportView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def get(self, request):
        kind = request.query_params.get("kind", "registrations")
        allowed = {
            "registrations",
            "activity",
            "farmers",
            "buyers",
            "geography",
            "engagement",
            "content",
        }
        if kind not in allowed:
            return Response(
                {"detail": "Choose a supported report type."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        period_days = request.query_params.get("days", "30")
        if period_days not in {"30", "180", "365"}:
            period_days = "30"
        start = timezone.now() - timedelta(days=int(period_days))
        if kind == "registrations":
            rows = list(
                User.objects.filter(date_joined__gte=start)
                .values(
                    "id",
                    "email",
                    "role",
                    "date_joined",
                    "is_verified",
                    "is_active",
                )
                .order_by("-date_joined")
            )
            title = "User registration report"
        elif kind == "activity":
            rows = list(
                _event_queryset()
                .filter(created_at__gte=start)
                .values(
                    "created_at",
                    "event_type",
                    "user_identifier",
                    "user_role",
                    "description",
                )
            )
            title = "User activity report"
        elif kind == "farmers":
            rows = list(
                User.objects.filter(role="farmer", date_joined__gte=start)
                .values("id", "email", "date_joined", "is_verified", "is_active")
                .order_by("-date_joined")
            )
            title = "Farmer registration report"
        elif kind == "buyers":
            rows = list(
                User.objects.filter(role="buyer", date_joined__gte=start)
                .values(
                    "id",
                    "email",
                    "date_joined",
                    "is_verified",
                    "is_active",
                    "profile__buyer_profile__buyer_type",
                )
                .order_by("-date_joined")
            )
            title = "Buyer registration report"
        elif kind == "geography":
            rows = list(
                Profile.objects.values(
                    "province", "district", "sector"
                )
                .annotate(users=Count("user_id"))
                .order_by("-users", "province", "district", "sector")
            )
            title = "User geographical distribution report"
        elif kind == "engagement":
            rows = list(
                _event_queryset()
                .filter(
                    event_type="login_success",
                    created_at__gte=start,
                    user_id__isnull=False,
                )
                .annotate(day=TruncDate("created_at"))
                .values("day")
                .annotate(
                    active_users=Count("user_id", distinct=True),
                    successful_logins=Count("id"),
                )
                .order_by("day")
            )
            title = "Platform engagement report"
        else:
            posts = BlogPost.objects.filter(
                is_published=True,
                published_at__gte=start,
            ).values(
                "title", "published_at"
            )
            listings = Product.objects.filter(
                is_active=True,
                verification_status="verified",
                created_at__gte=start,
            ).values(
                "name", "created_at", "verification_status"
            )
            rows = [
                {
                    "content_type": "post",
                    "title": item["title"],
                    "status": "published",
                    "created_at": item["published_at"],
                }
                for item in posts
            ] + [
                {
                    "content_type": "agricultural_listing",
                    "title": item["name"],
                    "status": item["verification_status"],
                    "created_at": item["created_at"],
                }
                for item in listings
            ]
            title = "Content publication report"

        generated_at = timezone.now()
        if request.query_params.get("export") == "csv":
            output = StringIO()
            fields = list(rows[0].keys()) if rows else ["message"]
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            if rows:
                writer.writerows(
                    {
                        field: _csv_safe(value)
                        for field, value in row.items()
                    }
                    for row in rows
                )
            else:
                writer.writerow({"message": "No records for the selected period."})
            response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = (
                f'attachment; filename="smartsave-{kind}-report.csv"'
            )
            return response
        return Response(
            {
                "kind": kind,
                "title": title,
                "generated_at": generated_at,
                "count": len(rows),
                "rows": rows[:500],
                "truncated": len(rows) > 500,
            }
        )


class AdminImpactView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def get(self, request):
        verified_paid_orders = Order.objects.filter(
            status="delivered", payment_status="paid"
        )
        connections = (
            OrderItem.objects.filter(
                order__in=verified_paid_orders,
                farmer_id__isnull=False,
            )
            .values("farmer_id", "order__buyer_id")
            .distinct()
            .count()
        )
        indicators = [
            {
                "key": "farmers",
                "label": "Farmers registered",
                "value": User.objects.filter(role="farmer").count(),
                "source": "Registered farmer accounts",
                "evidence": "Platform registration records",
            },
            {
                "key": "cooperatives",
                "label": "Cooperatives connected",
                "value": NGOProfile.objects.filter(
                    organization_type="cooperative"
                ).count(),
                "source": "Organization profiles classified as cooperatives",
                "evidence": "Organization classification; account verification is shown separately",
            },
            {
                "key": "buyers",
                "label": "Buyers connected",
                "value": User.objects.filter(role="buyer").count(),
                "source": "Registered buyer accounts",
                "evidence": "Platform registration records",
            },
            {
                "key": "institutional_partners",
                "label": "Institutional partners",
                "value": NGOProfile.objects.filter(
                    organization_type="institution"
                ).count()
                + User.objects.filter(
                    role="buyer",
                    profile__buyer_profile__buyer_type="institution",
                ).count(),
                "source": "Institution-classified organizations and institutional buyers",
                "evidence": "Profile classification",
            },
            {
                "key": "listings",
                "label": "Active agricultural listings",
                "value": Product.objects.filter(is_active=True).count(),
                "source": "Active product listings",
                "evidence": "Platform listing records",
            },
            {
                "key": "transactions",
                "label": "Completed paid orders",
                "value": verified_paid_orders.count(),
                "source": "Delivered orders with payment status paid",
                "evidence": "Order and payment records; not independently audited",
            },
            {
                "key": "market_connections",
                "label": "Farmer–buyer connections",
                "value": connections,
                "source": "Distinct farmer and buyer pairs with a delivered, paid order",
                "evidence": "Order line-item records",
            },
            {
                "key": "youth_participation",
                "label": "Youth participation",
                "value": None,
                "source": "Not measured",
                "evidence": "Age and consent evidence is not collected for this indicator",
            },
            {
                "key": "food_loss_reduction",
                "label": "Food loss reduction",
                "value": None,
                "source": "Not measured",
                "evidence": "No verified quantity and evidence tracking is available",
            },
        ]
        return Response(
            {
                "indicators": indicators,
                "disclaimer": (
                    "Counts reflect platform records only. They are not independent "
                    "impact evaluations. Indicators without documented evidence are "
                    "marked Not measured and are never estimated."
                ),
            }
        )


class AdminSettingsView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def get(self, request):
        administrators = User.objects.filter(is_staff=True).order_by("email")
        return Response(
            {
                "current_admin": {
                    "id": request.user.pk,
                    "email": request.user.email,
                    "name": request.user.get_full_name(),
                    "last_login": request.user.last_login,
                },
                "administrators": [
                    {
                        "id": user.pk,
                        "email": user.email,
                        "name": user.get_full_name(),
                        "is_active": user.is_active,
                        "last_login": user.last_login,
                    }
                    for user in administrators
                ],
                "access_policy": (
                    "Only active staff accounts can use administrative APIs. "
                    "Passwords, tokens and role-changing controls are not exposed here."
                ),
            }
        )


class PublicReportCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    TARGET_MODELS = {
        "user": User,
        "product": Product,
        "post": BlogPost,
        "recovery": RecoveryListing,
    }

    def post(self, request):
        target_type = request.data.get("target_type")
        target_id = request.data.get("target_id")
        reason = request.data.get("reason", "")
        model = self.TARGET_MODELS.get(target_type)
        if model is None:
            return Response(
                {"detail": "Unsupported report target."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            target_id = int(target_id)
        except (TypeError, ValueError):
            return Response(
                {"detail": "A valid target ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if target_id < 1 or not model.objects.filter(pk=target_id).exists():
            return Response(
                {"detail": "The reported item was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
            return Response(
                {"detail": "A report reason of 1–2000 characters is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report = ModerationReport.objects.create(
            reporter=request.user,
            target_type=target_type,
            target_id=target_id,
            reason=reason.strip(),
        )
        record_event(
            "security_event",
            request=request,
            user=request.user,
            description="Submitted a moderation report",
            metadata={"report_id": report.pk, "target_type": target_type},
        )
        return Response(
            ModerationReportSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )


class AdminReportsView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def get(self, request):
        reports = ModerationReport.objects.select_related("reporter").all()
        report_status = request.query_params.get("status", "open")
        if report_status in {"open", "resolved", "dismissed"}:
            reports = reports.filter(status=report_status)
        paginator = AdminPagination()
        page = paginator.paginate_queryset(reports, request, view=self)
        return paginator.get_paginated_response(
            ModerationReportSerializer(page, many=True).data
        )

    def patch(self, request, report_id):
        report = get_object_or_404(ModerationReport, pk=report_id)
        new_status = request.data.get("status")
        resolution = request.data.get("resolution", "")
        if new_status not in {"resolved", "dismissed"}:
            return Response(
                {"detail": "Status must be resolved or dismissed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(resolution, str) or not resolution.strip() or len(resolution) > 500:
            return Response(
                {"detail": "A resolution note of 1–500 characters is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report.status = new_status
        report.resolution = resolution.strip()
        report.resolved_by = request.user
        report.save(update_fields=["status", "resolution", "resolved_by", "updated_at"])
        AuditEvent.objects.create(
            event_type="admin_action",
            user=request.user,
            actor=request.user,
            user_identifier=request.user.email,
            user_role=request.user.role,
            description=f"Report #{report.pk} {new_status}: {report.resolution}",
            metadata={"report_id": report.pk, "status": new_status},
        )
        return Response(ModerationReportSerializer(report).data)


class AdminAnnouncementListView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def get(self, request):
        for announcement in Announcement.objects.filter(
            status="published",
            notifications_sent_at__isnull=True,
            visibility__in=["dashboard", "both"],
        ).filter(Q(publish_at__isnull=True) | Q(publish_at__lte=timezone.now())):
            _dispatch_announcement_notifications(announcement)
        announcements = Announcement.objects.all()
        status_filter = request.query_params.get("status", "").strip()
        if status_filter in {"draft", "published", "archived"}:
            announcements = announcements.filter(status=status_filter)
        return Response(AnnouncementSerializer(announcements[:100], many=True).data)

    def post(self, request):
        serializer = AnnouncementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement = serializer.save(
            created_by=request.user,
            updated_by=request.user,
        )
        _dispatch_announcement_notifications(announcement)
        AuditEvent.objects.create(
            event_type="admin_action",
            user=request.user,
            actor=request.user,
            user_identifier=request.user.email,
            user_role=request.user.role,
            description=f"Created announcement: {announcement.title}",
            metadata={"announcement_id": announcement.pk, "action": "create"},
        )
        return Response(
            AnnouncementSerializer(announcement).data,
            status=status.HTTP_201_CREATED,
        )


class AdminAnnouncementDetailView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def put(self, request, announcement_id):
        return self._update(request, announcement_id, partial=False)

    def patch(self, request, announcement_id):
        return self._update(request, announcement_id, partial=True)

    def delete(self, request, announcement_id):
        announcement = get_object_or_404(Announcement, pk=announcement_id)
        title = announcement.title
        announcement.delete()
        record_event(
            "admin_action",
            request=request,
            user=request.user,
            actor=request.user,
            description=f"Deleted announcement: {title}",
            metadata={"action": "delete"},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _update(self, request, announcement_id, partial):
        announcement = get_object_or_404(Announcement, pk=announcement_id)
        payload = request.data.copy()
        requested_status = payload.get("status")
        if requested_status in {"draft", "published", "archived"}:
            payload["status"] = requested_status
        elif "is_published" in payload:
            payload["status"] = "published" if payload["is_published"] else "draft"
        serializer = AnnouncementSerializer(
            announcement, data=payload, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        announcement = serializer.save(updated_by=request.user)
        _dispatch_announcement_notifications(announcement)
        AuditEvent.objects.create(
            event_type="admin_action",
            user=request.user,
            actor=request.user,
            user_identifier=request.user.email,
            user_role=request.user.role,
            description=f"Updated announcement: {announcement.title}",
            metadata={"announcement_id": announcement.pk, "action": announcement.status},
        )
        return Response(AnnouncementSerializer(announcement).data)


class PublicAnnouncementListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        now = timezone.now()
        surface = request.query_params.get("surface", "homepage")
        if surface not in {"homepage", "dashboard"}:
            return Response(
                {"detail": "surface must be homepage or dashboard."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for announcement in Announcement.objects.filter(
            status="published",
            notifications_sent_at__isnull=True,
            visibility__in=["dashboard", "both"],
        ).filter(Q(publish_at__isnull=True) | Q(publish_at__lte=now)):
            _dispatch_announcement_notifications(announcement)
        announcements = Announcement.objects.filter(
            status="published",
        ).filter(Q(publish_at__isnull=True) | Q(publish_at__lte=now)).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).filter(visibility__in=["both", surface])
        audience_filter = Q(audience="all")
        if request.user.is_authenticated:
            if request.user.role in {"farmer", "buyer", "ngo"}:
                audience_filter |= Q(audience=request.user.role)
            profile = Profile.objects.filter(user=request.user).select_related(
                "ngo_profile", "buyer_profile"
            ).first()
            if request.user.role == "ngo" and profile:
                organization_type = getattr(profile, "ngo_profile", None)
                if organization_type:
                    if organization_type.organization_type == "cooperative":
                        audience_filter |= Q(audience="cooperative")
                    if organization_type.organization_type == "institution":
                        audience_filter |= Q(audience="institution")
            buyer_profile = getattr(profile, "buyer_profile", None) if profile else None
            if request.user.role == "buyer" and buyer_profile and buyer_profile.buyer_type == "institution":
                audience_filter |= Q(audience="institution")
        announcements = announcements.filter(audience_filter).order_by(
            "-is_pinned", "-created_at"
        )
        return Response(AnnouncementSerializer(announcements[:20], many=True).data)


class AdminModerationView(APIView):
    permission_classes = [IsConfiguredAdmin]

    def get(self, request):
        items = []
        items.extend(
            {
                "id": item.pk,
                "item_type": "product",
                "type": "Product verification",
                "title": item.name,
                "status": item.verification_status,
                "created_at": item.created_at,
            }
            for item in Product.objects.filter(verification_status="pending").order_by("-created_at")[:50]
        )
        items.extend(
            {
                "id": item.pk,
                "item_type": "report",
                "type": "User report",
                "title": item.reason[:100],
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in ModerationReport.objects.filter(status="open").order_by("-created_at")[:50]
        )
        items.extend(
            {
                "id": item.pk,
                "item_type": "post",
                "type": "Blog post review",
                "title": item.title,
                "status": "draft",
                "created_at": item.created_at,
            }
            for item in BlogPost.objects.filter(is_published=False).order_by("-created_at")[:50]
        )
        items.extend(
            {
                "id": item.pk,
                "item_type": "comment",
                "type": "Comment review",
                "title": item.body[:100],
                "status": "pending",
                "created_at": item.created_at,
            }
            for item in BlogComment.objects.filter(is_approved=False).order_by("-created_at")[:50]
        )
        items.sort(key=lambda item: item["created_at"], reverse=True)
        return Response(items[:100])

    def patch(self, request, item_type, item_id):
        decision = request.data.get("decision")
        reason = request.data.get("reason", "")
        if item_type == "report":
            if decision not in {"approve", "reject"} or not isinstance(reason, str) or not reason.strip():
                return Response(
                    {"detail": "A decision and review reason are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            report = get_object_or_404(ModerationReport, pk=item_id, status="open")
            report.status = "resolved" if decision == "approve" else "dismissed"
            report.resolution = reason.strip()[:500]
            report.resolved_by = request.user
            report.save(update_fields=["status", "resolution", "resolved_by", "updated_at"])
            AuditEvent.objects.create(
                event_type="admin_action",
                user=request.user,
                actor=request.user,
                user_identifier=request.user.email,
                user_role=request.user.role,
                description=f"Report #{report.pk} {report.status}: {report.resolution}",
                metadata={"report_id": report.pk, "status": report.status},
            )
            return Response(ModerationReportSerializer(report).data)
        if decision not in {"approve", "reject"}:
            return Response(
                {"detail": "Decision must be approve or reject."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            return Response(
                {"detail": "A review reason of 1–500 characters is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if item_type == "product":
            item = get_object_or_404(Product, pk=item_id)
            item.verification_status = "verified" if decision == "approve" else "rejected"
            item.save(update_fields=["verification_status", "updated_at"])
            title = item.name
        elif item_type == "post":
            item = get_object_or_404(BlogPost, pk=item_id)
            item.is_published = decision == "approve"
            if item.is_published and item.published_at is None:
                item.published_at = timezone.now()
            item.save(update_fields=["is_published", "published_at", "updated_at"])
            title = item.title
        elif item_type == "comment":
            item = get_object_or_404(BlogComment, pk=item_id)
            item.is_approved = decision == "approve"
            item.save(update_fields=["is_approved"])
            title = f"Comment #{item.pk}"
        else:
            return Response(
                {"detail": "Unsupported moderation item."},
                status=status.HTTP_404_NOT_FOUND,
            )
        AuditEvent.objects.create(
            event_type="admin_action",
            user=request.user,
            actor=request.user,
            user_identifier=request.user.email,
            user_role=request.user.role,
            description=f"{decision.title()} {item_type}: {title}. {reason.strip()}",
            metadata={"item_type": item_type, "item_id": item_id, "decision": decision},
        )
        return Response({"detail": f"{item_type.title()} {decision}d."})
