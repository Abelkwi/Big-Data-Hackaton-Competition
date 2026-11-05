from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from accounts.models import Profile
from dashboard.models import Announcement, AuditEvent
from notifications.models import Notification


User = get_user_model()


@override_settings(ADMIN_LOGIN_EMAIL="admin@example.com")
class AdminPortalTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="platform-admin",
            email="admin@example.com",
            password="StrongPass123",
            role="admin",
            is_staff=True,
            is_verified=True,
        )
        self.farmer = User.objects.create_user(
            username="registered-farmer",
            email="farmer@example.com",
            password="NeverExposeThisPassword1",
            role="farmer",
            is_verified=True,
        )

    def test_admin_endpoints_require_staff_authorization(self):
        self.client.force_authenticate(user=self.farmer)

        response = self.client.get("/api/dashboard/admin/users/")

        self.assertEqual(response.status_code, 403)

    def test_overview_reports_growth_geography_and_unique_engagement(self):
        profile = Profile.objects.get(user=self.farmer)
        profile.province = "Kigali City"
        profile.district = "Gasabo"
        profile.sector = "Kimironko"
        profile.save()
        AuditEvent.objects.create(
            event_type="login_success",
            user=self.farmer,
            user_identifier=self.farmer.email,
        )
        AuditEvent.objects.create(
            event_type="login_success",
            user=self.farmer,
            user_identifier=self.farmer.email,
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            "/api/dashboard/admin/?period=7&geography_level=district"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["active_users"], 1)
        self.assertEqual(response.data["summary"]["returning_users_30d"], 1)
        self.assertEqual(response.data["analytics"]["engagement"]["daily_active_users"], 1)
        self.assertEqual(len(response.data["analytics"]["registrations"]), 7)
        self.assertEqual(response.data["analytics"]["geography_level"], "district")
        self.assertEqual(response.data["analytics"]["geography"][0]["location"], "Gasabo")

    def test_users_can_be_filtered_edited_verified_and_exported_without_secrets(self):
        profile = Profile.objects.get(user=self.farmer)
        profile.province = "Eastern"
        profile.save()
        self.client.force_authenticate(user=self.admin)

        listing = self.client.get("/api/dashboard/admin/users/?province=Eastern")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data["count"], 1)

        update = self.client.patch(
            f"/api/dashboard/admin/users/{self.farmer.pk}/",
            {"first_name": "Aline", "district": "Rwamagana"},
            format="json",
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data["first_name"], "Aline")
        self.assertEqual(update.data["profile"]["district"], "Rwamagana")

        verification = self.client.post(
            f"/api/dashboard/admin/users/{self.farmer.pk}/verify/",
            {"verified": False, "reason": "Supporting documents require review."},
            format="json",
        )
        self.assertEqual(verification.status_code, 200)
        self.farmer.refresh_from_db()
        self.assertFalse(self.farmer.is_verified)

        export = self.client.get("/api/dashboard/admin/users/?export=csv")
        self.assertEqual(export.status_code, 200)
        self.assertIn("text/csv", export["Content-Type"])
        self.assertIn("Aline", export.content.decode())
        self.assertNotIn("password", export.content.decode().lower())

    def test_impact_and_reports_expose_evidence_and_csv_exports(self):
        self.client.force_authenticate(user=self.admin)

        impact = self.client.get("/api/dashboard/admin/impact/")
        self.assertEqual(impact.status_code, 200)
        indicators = {row["key"]: row for row in impact.data["indicators"]}
        self.assertIsNone(indicators["food_loss_reduction"]["value"])
        self.assertEqual(indicators["food_loss_reduction"]["source"], "Not measured")
        self.assertEqual(indicators["farmers"]["value"], 1)

        report = self.client.get(
            "/api/dashboard/admin/insights/reports/?kind=farmers&export=csv"
        )
        self.assertEqual(report.status_code, 200, getattr(report, "data", None))
        self.assertIn("text/csv", report["Content-Type"])
        self.assertIn(self.farmer.email, report.content.decode())

    def test_dashboard_announcement_pin_and_targeted_notification_delivery(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/dashboard/admin/announcements/",
            {
                "title": "Farmer campaign",
                "body": "Registration is open.",
                "category": "important",
                "audience": "farmer",
                "visibility": "dashboard",
                "is_pinned": True,
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        announcement = Announcement.objects.get(pk=response.data["id"])
        self.assertTrue(announcement.is_pinned)
        self.assertIsNotNone(announcement.notifications_sent_at)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.farmer,
                notification_type="announcement",
                title="Farmer campaign",
            ).exists()
        )

        self.client.force_authenticate(user=self.farmer)
        dashboard = self.client.get("/api/dashboard/announcements/?surface=dashboard")
        homepage = self.client.get("/api/dashboard/announcements/?surface=homepage")
        self.assertEqual(dashboard.status_code, 200)
        self.assertTrue(dashboard.data[0]["is_pinned"])
        self.assertEqual(homepage.data, [])

    def test_targeted_homepage_announcements_only_show_to_the_intended_audience(self):
        announcement = Announcement.objects.create(
            title="Farmer homepage notice",
            body="Information for farmers.",
            category="general",
            audience="farmer",
            visibility="both",
            status="published",
            created_by=self.admin,
            updated_by=self.admin,
        )

        anonymous_response = self.client.get(
            "/api/dashboard/announcements/?surface=homepage"
        )
        self.assertEqual(anonymous_response.status_code, 200)
        self.assertEqual(anonymous_response.data, [])

        self.client.force_authenticate(user=self.farmer)
        farmer_response = self.client.get(
            "/api/dashboard/announcements/?surface=homepage"
        )
        self.assertEqual(farmer_response.status_code, 200)
        self.assertEqual([item["id"] for item in farmer_response.data], [announcement.pk])

    def test_staff_settings_endpoint_is_protected_and_excludes_secrets(self):
        self.client.force_authenticate(user=self.farmer)
        self.assertEqual(
            self.client.get("/api/dashboard/admin/settings/").status_code,
            403,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/dashboard/admin/settings/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["current_admin"]["email"], self.admin.email)
        self.assertNotIn("password", response.data["current_admin"])
        self.assertNotIn("password", response.data["administrators"][0])

    def test_user_api_search_status_and_detail_exclude_credentials(self):
        self.client.force_authenticate(user=self.admin)

        listing = self.client.get(
            "/api/dashboard/admin/users/?search=farmer&role=farmer&status=active"
        )
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data["count"], 1)
        self.assertNotIn("password", listing.data["results"][0])

        detail = self.client.get(f"/api/dashboard/admin/users/{self.farmer.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertNotIn("password", detail.data)
        self.assertNotIn("refresh", detail.data)
        self.assertNotIn("access", detail.data)
        self.assertEqual(detail.data["email"], self.farmer.email)

    def test_admin_can_suspend_and_activate_with_audited_reason(self):
        self.client.force_authenticate(user=self.admin)
        url = f"/api/dashboard/admin/users/{self.farmer.pk}/status/"

        suspended = self.client.post(
            url,
            {"status": "suspended", "reason": "Repeated fraudulent listings."},
            format="json",
        )
        self.assertEqual(suspended.status_code, 200)
        self.assertEqual(suspended.data["status"], "suspended")
        self.assertTrue(
            AuditEvent.objects.filter(
                event_type="account_suspension",
                actor=self.admin,
                user=self.farmer,
            ).exists()
        )

        activated = self.client.post(
            url,
            {"status": "active", "reason": "Appeal reviewed and resolved."},
            format="json",
        )
        self.assertEqual(activated.status_code, 200)
        self.assertEqual(activated.data["status"], "active")

    def test_admin_announcements_can_be_published_and_are_public(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/dashboard/admin/announcements/",
            {
                "title": "Farmer registration drive",
                "body": "Join the SMARTSAVE farmer network.",
                "category": "important",
                "audience": "all",
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["is_published"])
        self.assertEqual(
            Announcement.objects.get(pk=response.data["id"]).status,
            "published",
        )

        self.client.force_authenticate(user=None)
        public = self.client.get("/api/dashboard/announcements/")
        self.assertEqual(public.status_code, 200)
        self.assertEqual(public.data[0]["title"], "Farmer registration drive")

    def test_admin_activity_and_health_endpoints_are_staff_only_and_redacted(self):
        AuditEvent.objects.create(
            event_type="login_failed",
            user_identifier="missing@example.com",
            description="Failed sign-in attempt",
            metadata={"attempt": "failed"},
        )
        self.client.force_authenticate(user=self.admin)

        activity = self.client.get(
            "/api/dashboard/admin/activity/?event_type=login_failed"
        )
        self.assertEqual(activity.status_code, 200)
        self.assertEqual(activity.data["results"][0]["user_email"], "missing@example.com")
        self.assertNotIn("password", activity.data["results"][0])

        health = self.client.get("/api/dashboard/admin/health/")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.data["services"]["database"], "healthy")

    def test_reports_can_be_submitted_and_resolved_with_audit(self):
        self.client.force_authenticate(user=self.farmer)
        report = self.client.post(
            "/api/dashboard/reports/",
            {
                "target_type": "user",
                "target_id": self.admin.pk,
                "reason": "Test report for moderation.",
            },
            format="json",
        )
        self.assertEqual(report.status_code, 201)

        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/dashboard/admin/reports/{report.data['id']}/",
            {"status": "dismissed", "resolution": "Reviewed and dismissed."},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "dismissed")
        self.assertTrue(
            AuditEvent.objects.filter(
                event_type="admin_action",
                actor=self.admin,
                description__contains="Report #",
            ).exists()
        )
