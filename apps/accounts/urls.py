from django.urls import path

from apps.accounts.views import MeView, SiteAccessView

urlpatterns = [
    path("auth/site-access/", SiteAccessView.as_view(), name="site-access"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
]
