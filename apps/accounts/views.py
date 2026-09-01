import secrets

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.accounts.site_access import create_site_access_token, is_valid_site_access_token


class SiteAccessThrottle(AnonRateThrottle):
    scope = "site_access"


class SiteAccessView(APIView):
    """Report gate status and exchange the configured passcode for a signed token."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get_throttles(self):
        return [SiteAccessThrottle()] if self.request.method == "POST" else []

    def get(self, request):
        required = bool(settings.SITE_ACCESS_PASSCODE)
        token = request.headers.get("X-Site-Access", "")
        return Response(
            {
                "required": required,
                "authenticated": not required or is_valid_site_access_token(token),
            }
        )

    def post(self, request):
        configured_passcode = settings.SITE_ACCESS_PASSCODE
        if not configured_passcode:
            return Response({"required": False, "authenticated": True})

        supplied_passcode = request.data.get("passcode", "") if isinstance(request.data, dict) else ""
        if not isinstance(supplied_passcode, str) or not secrets.compare_digest(
            supplied_passcode,
            configured_passcode,
        ):
            return Response(
                {"detail": "Incorrect passcode."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "required": True,
                "authenticated": True,
                "token": create_site_access_token(),
                "expires_in": settings.SITE_ACCESS_TOKEN_MAX_AGE,
            }
        )


class MeView(APIView):
    """Returns the authenticated staff user's profile (for the admin/JWT flow)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        )
