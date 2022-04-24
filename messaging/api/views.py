import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from messaging.api.slack import auth
from messaging.api.slack.event import run
from messaging.api.slack.register import action_handler


@csrf_exempt
@require_http_methods(["POST"])
def slack_event(request):
    body = json.loads(request.body)
    run(body=body.get("event"))
    challenge = body.get("challenge")
    if challenge:
        return JsonResponse({"challenge": body.get("challenge")})
    return HttpResponse()


@csrf_exempt
@require_http_methods(["POST"])
def slack_action(request):
    body = json.loads(request.POST["payload"])
    action_handler(payload=body)
    challenge = body.get("challenge")
    if challenge:
        return JsonResponse({"challenge": body.get("challenge")})
    return HttpResponse()


@login_required
@require_http_methods(["GET"])
def slack_user_auth(request):
    code = request.GET["code"]
    auth.auth(code=code, user=request.user)
    return HttpResponseRedirect(reverse("user_dashboard"))
