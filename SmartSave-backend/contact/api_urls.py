from django.urls import path

from . import api_views

urlpatterns = [
    path("", api_views.ContactCreateView.as_view(), name="contact-create"),
    path("list/", api_views.ContactListView.as_view(), name="contact-list"),
    path("<int:id>/read/", api_views.MarkAsReadView.as_view(), name="contact-mark-read"),
]
