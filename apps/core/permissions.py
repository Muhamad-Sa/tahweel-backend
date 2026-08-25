from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStaffOrReadOnly(BasePermission):
    """Public read access; write access restricted to staff users.

    This is the default permission for the whole API: catalogue browsing
    (products, documents, categories, catalogues, search) is public, while
    mutating endpoints (document upload, revision management, etc.) require
    an authenticated staff/admin account (JWT).
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
