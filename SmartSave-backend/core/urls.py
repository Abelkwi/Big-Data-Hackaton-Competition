from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from .views import serve_static_page

# Path to the ClaudeWEB2 frontend folder (only used for local development)
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "ClaudeWEB2"
FRONTEND_EXISTS = FRONTEND_DIR.exists()

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # API root
    path("api/", include("core.api_urls")),

    # App-level URLs (template-based)
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("marketplace/", include(("marketplace.urls", "marketplace"), namespace="marketplace")),
]

# Static page serving - only when the frontend folder is present (local dev)
# On Render production, the frontend is hosted separately and only the API is served.
if FRONTEND_EXISTS:
    urlpatterns += [
        # Home
        path("", serve_static_page, {"page": "index.html"}, name="home"),
        path("about/", serve_static_page, {"page": "about.html"}, name="about"),
        path("blog/", serve_static_page, {"page": "blog.html"}, name="blog"),
        path("blog-post/", serve_static_page, {"page": "blog-post.html"}, name="blog_post"),
        path("contact/", serve_static_page, {"page": "contact.html"}, name="contact"),
        path("cooperative-profile/", serve_static_page, {"page": "cooperative-profile.html"}, name="cooperative_profile"),
        path("farmer-profile/", serve_static_page, {"page": "farmer-profile.html"}, name="farmer_profile"),
        path("farmers/", serve_static_page, {"page": "farmers.html"}, name="farmers"),
        path("innovation/", serve_static_page, {"page": "innovation.html"}, name="innovation"),
        path("login/", serve_static_page, {"page": "login.html"}, name="login_page"),
        path("marketplace-product/", serve_static_page, {"page": "marketplace-product.html"}, name="marketplace_product"),
        path("marketplace.html", serve_static_page, {"page": "marketplace.html"}, name="marketplace_page"),
        path("recovery/", serve_static_page, {"page": "recovery.html"}, name="recovery"),
        path("register/", serve_static_page, {"page": "register.html"}, name="register_page"),
        path("register-buyer/", serve_static_page, {"page": "register-buyer.html"}, name="register_buyer_page"),
        path("register-farmer/", serve_static_page, {"page": "register-farmer.html"}, name="register_farmer_page"),
        path("register-ngo/", serve_static_page, {"page": "register-ngo.html"}, name="register_ngo_page"),
        path("buyer-dashboard/", serve_static_page, {"page": "buyer-dashboard.html"}, name="buyer_dashboard"),
        path("404/", serve_static_page, {"page": "404.html"}, name="not_found"),
    ]

if settings.DEBUG and FRONTEND_EXISTS:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve ClaudeWEB2 static assets (js/, Fonts/, Logo.png, etc.) from the frontend folder
    urlpatterns += [
        re_path(
            r"^(?P<path>(?:js|assets|fonts|Fonts|css|images)/.*)$",
            serve,
            {"document_root": FRONTEND_DIR, "show_indexes": True},
            name="frontend-static",
        ),
        re_path(
            r"^(?P<path>.*\.(png|jpg|jpeg|gif|svg|ico|css|js|ttf|woff|woff2))$",
            serve,
            {"document_root": FRONTEND_DIR},
            name="frontend-files",
        ),
    ]