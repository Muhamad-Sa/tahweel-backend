from django.conf import settings
from django.core import signing


SITE_ACCESS_SALT = "tahweel.site-access"


def _signing_salt():
    # Binding the signature to the current passcode makes changing the
    # passcode immediately revoke every token issued for the old one.
    return f"{SITE_ACCESS_SALT}.{settings.SITE_ACCESS_PASSCODE}"


def create_site_access_token():
    """Return a signed, time-limited proof that the passcode was accepted."""

    return signing.dumps({"site_access": True}, salt=_signing_salt(), compress=True)


def is_valid_site_access_token(token):
    if not token:
        return False

    try:
        payload = signing.loads(
            token,
            salt=_signing_salt(),
            max_age=settings.SITE_ACCESS_TOKEN_MAX_AGE,
        )
    except signing.BadSignature:
        return False

    return payload == {"site_access": True}
