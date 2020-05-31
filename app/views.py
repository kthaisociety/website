import hmac
import json
import os
import subprocess
from _sha1 import sha1
from ipaddress import ip_address, ip_network

from django.contrib.auth.decorators import login_required
from django.http import (
    StreamingHttpResponse,
    HttpResponseNotFound,
)
from django.shortcuts import render
from django.utils.encoding import force_bytes
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import requests

from app import settings
from app.settings import GH_KEY, GH_BRANCH
from app.slack import send_deploy_message
from event.utils import get_user_registrations


def home(request):
    return render(request, "home.html", {})


def maintenance(request):
    return render(request, "maintenance.html", {})


@login_required
def dashboard(request):
    registrations = get_user_registrations(request.user.id)
    return render(request, "dashboard.html", {"registrations": registrations})


def files(request, file_):
    path, file_name = os.path.split(file_)
    if request.user.is_authenticated:
        if path in ["user/picture", "__sized__/user/picture"]:
            if file_[:7] != "/files/":
                file_ = "/files/" + file_
            response = StreamingHttpResponse(open(settings.BASE_DIR + file_, "rb"))
            response["Content-Type"] = ""
            return response
        else:
            HttpResponseNotFound()
    if path in [
        "news/article",
        "__sized__/news/article",
        "event/picture",
        "__sized__/event/picture",
        "event/attachment/file",
        "event/attachment/preview",
        "__sized__/event/attachment/preview",
    ]:
        if file_[:7] != "/files/":
            file_ = "/files/" + file_
        response = StreamingHttpResponse(open(settings.BASE_DIR + file_, "rb"))
        response["Content-Type"] = ""
        return response
    else:
        HttpResponseNotFound()
    # return HttpResponseRedirect("%s?next=%s" % (reverse("user_login"), request.path))


@require_POST
@csrf_exempt
def deploy(request):
    forwarded_for = u"{}".format(request.META.get("HTTP_X_FORWARDED_FOR"))
    client_ip_address = ip_address(forwarded_for)
    whitelist = requests.get("https://api.github.com/meta").json()["hooks"]

    for valid_ip in whitelist:
        if client_ip_address in ip_network(valid_ip):
            break
    else:
        return response(request, code=500)

    header_signature = request.META.get("HTTP_X_HUB_SIGNATURE")
    if header_signature is None:
        return response(request, code=500)

    sha_name, signature = header_signature.split("=")
    if sha_name != "sha1":
        return response(request, code=501)

    mac = hmac.new(force_bytes(GH_KEY), msg=force_bytes(request.body), digestmod=sha1)
    if not hmac.compare_digest(force_bytes(mac.hexdigest()), force_bytes(signature)):
        return response(request, code=500)

    event = request.META.get("HTTP_X_GITHUB_EVENT")
    if event == "push":
        data = json.loads(request.body.decode("utf-8"))
        # Deploy if push to the current branch
        if data["ref"] == "refs/heads/" + GH_BRANCH:
            try:
                subprocess.call(
                    os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), "../deploy.sh"
                    )
                )
                send_deploy_message(data, succedded=True)
            except OSError:
                send_deploy_message(data, succedded=False)
            return response(request, code=200)
    return response(request, code=204)


def response(request, *args, code: int, message: str = None, **kwargs):
    response_result = render(request, "response.html", dict(code=code, message=message))
    response_result.status_code = code
    return response_result


def response_400(request, *args, **kwargs):
    return response(request, *args, code=404, *kwargs)


def response_403(request, *args, **kwargs):
    return response(request, *args, code=404, *kwargs)


def response_404(request, *args, **kwargs):
    return response(request, *args, code=404, *kwargs)


def response_500(request, *args, **kwargs):
    return response(request, *args, code=404, *kwargs)
