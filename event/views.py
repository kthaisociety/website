from django.contrib import messages
from django.http import HttpResponseNotFound, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from event.enums import RegistrationStatus
from event.models import Event, Registration


def event(request, code):
    event = Event.objects.published().filter(code=code).first()
    if request.user.is_authenticated:
        registration = Registration.objects.filter(event=event, user=request.user).first()
    else:
        registration = None

    if event:
        if request.method == "POST":
            if not request.user.is_authenticated:
                return HttpResponseRedirect(reverse("user_login"))

            type = request.POST.get("submit", None)
            if type == "register":
                messages.success(request, f"You've been registered! Remember the event will take place on {event.starts_at.strftime('%B %-d, %Y')}.")
                status = RegistrationStatus.REQUESTED
            elif type == "interest":
                messages.success(request, f"Thank-you for letting us know, we hope to wee you in a future event!")
                status = RegistrationStatus.INTERESTED
            elif type == "cancel":
                messages.success(request, f"Thank-you for letting us know, we hope to wee you in a future event!")
                status = RegistrationStatus.CANCELLED
            else:
                status = None

            if status is not None:
                if registration:
                    registration.status = status
                    registration.save()
                else:
                    registration = Registration.objects.create(event=event, user=request.user, status=status)

        return render(request, "event.html", {"event": event, "registration": registration})
    return HttpResponseNotFound()


def events(request):
    return HttpResponseRedirect(reverse("app_home"))


def event_ics(request, code):
    event = Event.objects.published().filter(code=code).first()
    if event:
        response = HttpResponse(event.ics, content_type="text/calendar")
        response["Content-Disposition"] = f"attachment; filename={code}.ics"
        return response
    return HttpResponseNotFound()
