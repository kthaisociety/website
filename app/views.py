import hmac
import json
import os
import subprocess
from collections import Counter, defaultdict
from ipaddress import ip_address, ip_network
from typing import Optional

import requests
from _sha1 import sha1
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import DateField
from django.db.models.functions import Cast
from django.http import HttpResponseNotFound, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import user.api.team
from app import settings
from app.settings import GH_BRANCH, GH_KEY
from app.slack import send_deploy_message
from event.enums import EventStatus, RegistrationStatus
from event.models import Registration, Session
from user.enums import GenderType, UserType
from user.models import User


def home(request):
    return render(request, "home.html", {})


def maintenance(request):
    return render(request, "maintenance.html", {})


def files(request, file_):
    path, file_name = os.path.split(file_)
    if request.user.is_authenticated:
        if path in [
            "user/picture",
            "__sized__/user/picture",
            "user/slack/picture",
            "__sized__/user/slack/picture",
        ]:
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
        "news/pin",
        "__sized__/news/pin",
        "news/fact",
        "__sized__/news/fact",
        "event/picture",
        "__sized__/event/picture",
        "event/attachment/file",
        "event/attachment/preview",
        "__sized__/event/attachment/preview",
        "event/speaker/picture",
        "__sized__/event/speaker/picture",
        "page/page",
        "__sized__/page/page",
        "page/picture",
        "__sized__/page/picture",
        "business/company/logo",
        "__sized__/business/company/logo",
        "user/role/picture",
        "__sized__/user/role/picture",
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
    forwarded_for = "{}".format(request.META.get("HTTP_X_FORWARDED_FOR"))
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


@login_required
@staff_member_required
def statistics(request):
    user_creation_dates = (
        User.objects.filter(is_active=True)
        .exclude(type=UserType.ORGANISER)
        .annotate(creation_date=Cast("created_at", DateField()))
        .values_list("creation_date", "email_verified", "registration_finished")
        .order_by("creation_date")
    )
    user_creation_dates_counter = Counter([d for d, _, _ in user_creation_dates])
    user_creation_dates_verified_counter = Counter(
        [d for d, ver, _ in user_creation_dates if ver]
    )
    user_creation_dates_finished_counter = Counter(
        [d for d, _, fin in user_creation_dates if fin]
    )
    stats_members = []
    stats_members_verified = []
    stats_members_finished = []
    stats_new_members = []
    stats_new_members_verified = []
    stats_new_members_finished = []
    if user_creation_dates:
        current_date = user_creation_dates[0][0]
        while current_date <= timezone.localdate(timezone.now()):
            stats_members.append(
                (
                    current_date,
                    (stats_members[-1][1] if stats_members else 0)
                    + user_creation_dates_counter.get(current_date, 0),
                )
            )
            stats_members_verified.append(
                (
                    current_date,
                    (stats_members_verified[-1][1] if stats_members_verified else 0)
                    + user_creation_dates_verified_counter.get(current_date, 0),
                )
            )
            stats_members_finished.append(
                (
                    current_date,
                    (stats_members_finished[-1][1] if stats_members_finished else 0)
                    + user_creation_dates_finished_counter.get(current_date, 0),
                )
            )
            stats_new_members.append(
                (
                    current_date,
                    user_creation_dates_counter.get(current_date, 0)
                    - user_creation_dates_finished_counter.get(current_date, 0),
                )
            )
            stats_new_members_verified.append(
                (
                    current_date,
                    user_creation_dates_verified_counter.get(current_date, 0)
                    - user_creation_dates_finished_counter.get(current_date, 0),
                )
            )
            stats_new_members_finished.append(
                (
                    current_date,
                    user_creation_dates_finished_counter.get(current_date, 0),
                )
            )
            current_date += timezone.timedelta(days=1)

    sessions = list(
        Session.objects.filter(event__status=EventStatus.PUBLISHED).order_by(
            "starts_at"
        )
    )

    registration_creation_dates = (
        Registration.objects.filter(
            status__in=[RegistrationStatus.REGISTERED, RegistrationStatus.JOINED]
        )
        .exclude(user__type=UserType.ORGANISER)
        .annotate(creation_date=Cast("created_at", DateField()))
        .values_list("creation_date", "status")
        .order_by("creation_date")
    )
    registration_creation_dates_counter_registered = Counter(
        [
            d
            for d, s in registration_creation_dates
            if s == RegistrationStatus.REGISTERED
        ]
    )
    registration_creation_dates_counter_joined = Counter(
        [d for d, s in registration_creation_dates if s == RegistrationStatus.JOINED]
    )
    stats_new_registrations_registered = []
    stats_new_registrations_joined = []
    if registration_creation_dates or sessions:
        current_date = (
            timezone.localdate(sessions[0].starts_at)
            if sessions
            else registration_creation_dates[0][0]
        )
        while current_date <= (
            (
                timezone.localdate(sessions[-1].starts_at)
                if sessions[-1].starts_at > timezone.now()
                else timezone.localdate(timezone.now())
            )
            if sessions
            else timezone.localdate(timezone.now())
        ):
            stats_new_registrations_registered.append(
                (
                    current_date,
                    registration_creation_dates_counter_registered.get(current_date, 0),
                )
            )
            stats_new_registrations_joined.append(
                (
                    current_date,
                    registration_creation_dates_counter_joined.get(current_date, 0),
                )
            )
            current_date += timezone.timedelta(days=1)

    for session in sessions:
        session.registrations_same_day = (
            registration_creation_dates_counter_registered.get(
                timezone.localdate(session.starts_at), 0
            )
            + registration_creation_dates_counter_joined.get(
                timezone.localdate(session.starts_at), 0
            )
        )

    users = list(User.objects.filter(is_active=True).exclude(type=UserType.ORGANISER))

    stats_members_gender = {gt: 0 for gt in GenderType}
    stats_members_year = defaultdict(int)
    stats_members_university = defaultdict(int)
    stats_members_programme = defaultdict(int)
    for u in users:
        stats_members_gender[u.gender] += 1
        if u.birthday:
            stats_members_year[u.birthday.year] += 1
        if u.university:
            stats_members_university[u.university] += 1
        if u.degree:
            stats_members_programme[u.degree] += 1

    stats_members_year = sorted(
        ((year, val) for year, val in stats_members_year.items()),
        key=lambda smy: smy[0],
    )
    stats_members_university = sorted(
        ((year, val) for year, val in stats_members_university.items()),
        key=lambda smy: -smy[1],
    )
    stats_members_programme = sorted(
        ((year, val) for year, val in stats_members_programme.items()),
        key=lambda smy: -smy[1],
    )

    return render(
        request,
        "statistics.html",
        {
            "statistics": {
                "members": stats_members,
                "members_verified": stats_members_verified,
                "members_finished": stats_members_finished,
                "members_gender": stats_members_gender,
                "stats_members_year": stats_members_year,
                "stats_members_university": stats_members_university,
                "stats_members_programme": stats_members_programme,
                "new_members": stats_new_members,
                "new_members_verified": stats_new_members_verified,
                "new_members_finished": stats_new_members_finished,
                "new_registrations_registered": stats_new_registrations_registered,
                "new_registrations_joined": stats_new_registrations_joined,
            },
            "sessions": sessions,
            "zoom": [
                timezone.localdate(timezone.now() - timezone.timedelta(days=30)),
                timezone.localdate(timezone.now()),
            ],
        },
    )


def about_team(request, code: Optional[str] = None):
    if request.method == "POST":
        team_code = request.POST.get("team")
        return redirect(reverse("app_about_team", args=(team_code,)))

    teams = user.api.team.get_teams()
    team = user.api.team.get_team(code=code)
    if team:
        return render(request, "about_team.html", {"team": team, "teams": teams})
    return HttpResponseNotFound()


def about_contact(request):
    return render(request, "about_contact.html")
