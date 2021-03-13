import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from messaging.api.slack.event import run


@csrf_exempt
@require_http_methods(["POST"])
def slack_event(request):
    body = json.loads(request.body)
    event_type = body.get("type")
    if event_type == "event_callback":
        run(body=body.get("event"))
    return JsonResponse(
        {"challenge": body.get("challenge")}
    )
