from typing import Any

from django.utils.deprecation import MiddlewareMixin


class CsrfExemptMiddleware(MiddlewareMixin):
    """
    Middleware to exempt API views from CSRF protection.
    """

    def process_request(self, request: Any) -> None:
        # Exempt all API views from CSRF
        if request.path.startswith("/api/") or request.path.startswith("/admin"):
            setattr(request, "_dont_enforce_csrf_checks", True)
        return None
