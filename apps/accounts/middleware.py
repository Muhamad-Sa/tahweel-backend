from django.conf import settings
from django.http import JsonResponse

from apps.accounts.site_access import is_valid_site_access_token


class SiteAccessMiddleware:
    """Protect API content when the optional site-wide passcode is enabled."""

    access_path = "/api/v1/auth/site-access/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        passcode_enabled = bool(settings.SITE_ACCESS_PASSCODE)
        is_protected_api = request.path.startswith("/api/v1/")
        is_exempt = request.path == self.access_path or request.method == "OPTIONS"

        if passcode_enabled and is_protected_api and not is_exempt:
            token = request.headers.get("X-Site-Access", "")
            if not is_valid_site_access_token(token):
                return JsonResponse(
                    {
                        "detail": "A valid site access passcode is required.",
                        "code": "site_access_required",
                    },
                    status=403,
                )

        return self.get_response(request)
