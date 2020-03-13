from django.urls import reverse

from app.settings import MAINTENANCE_MODE
from app.views import maintenance
from user.views import user_register


class RegisterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and (not request.user.email_verified or not request.user.registration_finished) and request.path != reverse("user_logout"):
            return user_register(request)
        return self.get_response(request)


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            MAINTENANCE_MODE
            and not (request.user.is_authenticated and request.user.is_organiser)
            and not any(
                [
                    request.path.startswith(p)
                    for p in ["/files", "/admin", "/page/legal", "/deploy", "/user/complete", "/user/login", "/user/logout"]
                ]
            )
        ):
            return maintenance(request)
        return self.get_response(request)
