from app.settings import MAINTENANCE_MODE
from app.views import maintenance


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
                    for p in ["/files/", "/admin/", "/page/legal/"]
                ]
            )
        ):
            return maintenance(request)
        return self.get_response(request)
