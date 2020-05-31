from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponseNotFound, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

import user.utils

from event.enums import RegistrationStatus
from event.models import Event, Registration
from event.tasks import send_registration_email


def event(request, code):
    event = Event.objects.published().filter(code=code).first()
    if request.user.is_authenticated:
        registration = Registration.objects.filter(
            event=event, user=request.user
        ).first()
    else:
        registration = None

    form = {}

    if event:
        if request.method == "POST" and event.registration_available:
            type = request.POST.get("submit", None)

            if type != "register" and not request.user.is_authenticated:
                return HttpResponseRedirect(reverse("user_login"))

            user_obj = request.user

            if type == "register":
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

            if status is not None:
                if registration:
                    registration.status = status
                    registration.save()
                else:
                    try:
                        registration = Registration.objects.create(
                            event=event, user=user_obj, status=status
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


def events(request):
    event_objs = Event.objects.published()
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
