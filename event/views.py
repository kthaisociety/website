from collections import defaultdict
from io import BytesIO

import qrcode
import qrcode.image.svg

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Subquery, OuterRef, Count, Value, Prefetch
from django.db.models.functions import Coalesce, Lower
from django.http import (
    HttpResponseNotFound,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from django.conf import settings

import user.utils
from event.api.event.registration import get_event_data_csv

from event.enums import RegistrationStatus, ScheduleType
from event.models import Event, Registration, Session, Schedule
from event.tasks import send_registration_email
from user.enums import DietType, UserType


def event(request, code, is_late: bool = False):
    event = Event.objects.published().filter(code=code).first()
    if request.user.is_authenticated:
        registration = Registration.objects.filter(
            event=event, user=request.user
        ).first()
    else:
        registration = None

    form = {}

    if event:
        if request.method == "POST" and (
            (not is_late and event.registration_available) or is_late
        ):
            type = request.POST.get("submit", None)

            if type != "register" and not request.user.is_authenticated:
                return HttpResponseRedirect(reverse("user_login"))

            user_obj = request.user

            diet = ""
            diet_other = ""

            resume = request.FILES.get("resume")

            if type == "register":
                diet_types = set()
                for dt in DietType:
                    if request.POST.get(f"diet_{dt.name.lower()}", False):
                        diet_types.add(dt)
                diet = ",".join([str(dt.value) for dt in diet_types])
                diet_other = request.POST.get("diet_other_custom", None)

                if DietType.OTHER in diet_types and not diet_other:
                    messages.error(
                        request,
                        "You must specify your other diet restrictions if you have any.",
                    )
                    status = None
                elif (
                    event.collect_resume
                    and not resume
                    and not (user_obj.is_authenticated and user_obj.resume)
                ):
                    messages.error(
                        request,
                        "You must provide a resume in order to register for this event.",
                    )
                    status = None
                else:
                    if not user_obj.is_authenticated:
                        name = request.POST.get("name", None)
                        surname = request.POST.get("surname", None)
                        email = request.POST.get("email", None)
                        form = {"name": name, "surname": surname, "email": email}

                        if not name or not surname or not email:
                            messages.error(
                                request,
                                "All fields are required, if you are already have an account you can login first.",
                            )

                        if email:
                            email = email.lower()

                        user_obj = user.utils.get_user_by_email(email=email)
                        if not user_obj:
                            user_obj = user.utils.create_user(
                                name=name, surname=surname, email=email
                            )
                            user.utils.send_imported(user=user_obj)
                        if not user_obj.name or not user_obj.surname:
                            user_obj.name = name
                            user_obj.surname = surname
                            user_obj.save()
                    messages.success(
                        request,
                        f"You've been registered! Remember the event will take place on {event.starts_at.strftime('%B %-d, %Y')}.",
                    )
                    # TODO: Temporal set to REGISTERED instead before organiser check is implemented
                    status = RegistrationStatus.REGISTERED
            elif type == "interest":
                messages.success(
                    request,
                    f"Thank-you for letting us know, we hope to see you in a future event!",
                )
                status = RegistrationStatus.INTERESTED
            elif type == "cancel":
                messages.success(
                    request,
                    f"Thank-you for letting us know, we hope to see you in a future event!",
                )
                status = RegistrationStatus.CANCELLED
            else:
                status = None

            if user_obj.is_authenticated:
                has_updated = False
                if diet != user_obj.diet or diet_other != user_obj.diet_other:
                    user_obj.diet = diet
                    user_obj.diet_other = diet_other
                    has_updated = True
                if resume:
                    user_obj.resume = resume
                    has_updated = True
                if has_updated:
                    user_obj.save()

            if status is not None:
                if registration:
                    registration.status = status
                    registration.diet = diet
                    registration.diet_other = diet_other
                    registration.save()
                else:
                    try:
                        registration = Registration.objects.create(
                            event=event,
                            user=user_obj,
                            status=status,
                            diet=diet,
                            diet_other=diet_other,
                        )
                    except IntegrityError:
                        registration = Registration.objects.filter(
                            event=event, user=user_obj
                        ).first()
                if registration:
                    send_registration_email(registration_id=registration.id)

        return render(
            request,
            "event.html",
            {"event": event, "registration": registration, "form": form},
        )
    return HttpResponseNotFound()


def live(request, code):
    # TODO: Get current instead of first
    sessions = list(
        Session.objects.published()
        .filter(
            event__code=code,
            ends_at__gte=timezone.now() - timezone.timedelta(minutes=30),
        )
        .order_by("ends_at")
        .all()
    )
    schedules = list(
        Schedule.objects.filter(session__in=sessions)
        .order_by("starts_at", "ends_at")
        .all()
    )
    starts_at = sessions[0].starts_at
    ends_at = sessions[-1].ends_at
    schedule_dict = defaultdict(list)
    start_time = starts_at.replace(minute=0, second=0)
    first_session_id = None
    while start_time <= ends_at:
        schedule_dict[start_time] = []
        start_time += timezone.timedelta(hours=1)
    for schedule in schedules:
        current_session_id = schedule.session_id
        if (
            not first_session_id or first_session_id == current_session_id
        ) and timezone.now() - timezone.timedelta(
            minutes=30
        ) <= schedule.session.ends_at:
            first_session_id = current_session_id
            if schedule.type == ScheduleType.EVENT_START:
                starts_at = schedule.starts_at
            elif schedule.type == ScheduleType.EVENT_END:
                ends_at = schedule.starts_at
        schedule_starts_at = schedule.starts_at.replace(minute=0, second=0)
        schedule_dict[schedule_starts_at].append(schedule)
    duration = ends_at - starts_at
    schedules = sorted(
        [
            {
                "starts_at": t,
                "ends_at": t + timezone.timedelta(hours=1),
                "schedules": ss,
            }
            for t, ss in schedule_dict.items()
        ],
        key=lambda el: el["starts_at"],
    )
    return render(
        request,
        "live.html",
        {
            "sessions": sessions,
            "now": timezone.now(),
            "schedules": schedules,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "duration": duration,
        },
    )


def events(request):
    event_objs = Event.objects.published().order_by("-created_at")
    return render(request, "events.html", {"events": event_objs})


def event_ics(request, code):
    event = Event.objects.published().filter(code=code).first()
    if event:
        response = HttpResponse(event.ics, content_type="text/calendar")
        response["Content-Disposition"] = f"attachment; filename={code}.ics"
        return response
    return HttpResponseNotFound()


def registration_url(request, registration_id):
    registration = Registration.objects.filter(id=registration_id).first()
    if registration and registration.event.external_url:
        registration.status = RegistrationStatus.JOINED
        registration.save()
        return HttpResponseRedirect(registration.event.external_url)
    return HttpResponseNotFound()


@login_required
@staff_member_required
def checkin_events(request):
    event_objs = (
        Event.objects.published()
        .prefetch_related("registrations")
        .annotate(
            registrations_pending_students=Coalesce(
                Subquery(
                    Registration.objects.filter(
                        event_id=OuterRef("id"),
                        status__in=[
                            RegistrationStatus.REGISTERED,
                        ],
                    )
                    .exclude(user__type=UserType.ORGANISER)
                    .values("event_id")
                    .annotate(count=Count("id"))
                    .values_list("count", flat="True")[:1]
                ),
                Value(0),
            ),
            registrations_pending_us=Coalesce(
                Subquery(
                    Registration.objects.filter(
                        event_id=OuterRef("id"),
                        status__in=[
                            RegistrationStatus.REGISTERED,
                        ],
                        user__type=UserType.ORGANISER,
                    )
                    .values("event_id")
                    .annotate(count=Count("id"))
                    .values_list("count", flat="True")[:1]
                ),
                Value(0),
            ),
            registrations_joined_all=Coalesce(
                Subquery(
                    Registration.objects.filter(
                        event_id=OuterRef("id"),
                        status__in=[
                            RegistrationStatus.JOINED,
                            RegistrationStatus.ATTENDED,
                        ],
                    )
                    .values("event_id")
                    .annotate(count=Count("id"))
                    .values_list("count", flat="True")[:1]
                ),
                Value(0),
            ),
            registrations_cancelled_all=Coalesce(
                Subquery(
                    Registration.objects.filter(
                        event_id=OuterRef("id"),
                        status__in=[
                            RegistrationStatus.CANCELLED,
                        ],
                    )
                    .values("event_id")
                    .annotate(count=Count("id"))
                    .values_list("count", flat="True")[:1]
                ),
                Value(0),
            ),
        )
        .order_by("-created_at")
    )
    return render(request, "checkin_events.html", {"events": event_objs})


@login_required
@staff_member_required
def checkin_event(request, code):
    event_obj = (
        Event.objects.filter(code=code)
        .prefetch_related(
            Prefetch(
                "registrations",
                Registration.objects.select_related("user").order_by(
                    "status", Lower("user__name"), Lower("user__surname")
                ),
                to_attr="all_registrations",
            ),
        )
        .first()
    )
    if event_obj:
        return render(request, "checkin_event.html", {"event": event_obj})
    return HttpResponseNotFound()


@login_required
@staff_member_required
def checkin_event_attend(request, registration_id):
    registration_obj = Registration.objects.filter(id=registration_id).first()
    if not registration_obj:
        return JsonResponse({"error": True})
    if registration_obj.status == RegistrationStatus.ATTENDED:
        registration_obj.status = RegistrationStatus.REGISTERED
    else:
        registration_obj.status = RegistrationStatus.ATTENDED
    registration_obj.save()
    return JsonResponse({"error": False, "status": registration_obj.status.value})


@login_required
@staff_member_required
def checkin_event_qr(request, code):
    event_obj = Event.objects.published().filter(code=code).first()
    if event_obj:
        factory = qrcode.image.svg.SvgImage
        img = qrcode.make(
            settings.APP_FULL_DOMAIN
            + reverse("events_checkin_event_register", args=(event_obj.id,)),
            image_factory=factory,
            box_size=20,
        )
        stream = BytesIO()
        img.save(stream)
        return render(
            request,
            "checkin_event_qr.html",
            context={"event": event_obj, "qr": stream.getvalue().decode()},
        )
    return HttpResponseNotFound()


def checkin_event_register(request, event_id):
    event_obj = Event.objects.published().filter(id=event_id).first()
    if (
        event_obj
        and event_obj.starts_at <= timezone.now() + timezone.timedelta(hours=6)
        and event_obj.ends_at >= timezone.now() - timezone.timedelta(hours=6)
    ):
        if request.method == "POST":
            return event(request=request, code=event_obj.code, is_late=True)
        registration_obj = None
        if request.user.is_authenticated:
            registration_obj = Registration.objects.filter(
                event=event_obj, user=request.user
            ).first()
        return render(
            request,
            "checkin_event_register.html",
            context={"event": event_obj, "registration": registration_obj},
        )
    return HttpResponseNotFound()


@login_required
@staff_member_required
def checkin_event_download(request, event_id):
    event_obj = Event.objects.published().filter(id=event_id).first()
    if event_obj:
        data = get_event_data_csv(event_id=event_id)
        response = HttpResponse(data.getvalue(), content_type="text/csv")
        file_name = f"{settings.APP_NAME.replace(' ', '').lower()}_data_{str(event_id)}_{str(int(timezone.now().timestamp()))}.csv"
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        return response
    return HttpResponseNotFound()
