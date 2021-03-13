import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["POST"])
def slack_event(request):
    body = json.loads(request.body)
    return JsonResponse(
        {"challenge": body.get("challenge")}
    )
