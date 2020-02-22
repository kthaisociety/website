from django.http import HttpResponseNotFound, HttpResponse
from django.shortcuts import render

from event.models import Event


def event(request, code):
    event = Event.objects.published().filter(code=code).first()
    if event:
        return render(request, "event.html", {"event": event})
    return HttpResponseNotFound()


def event_ics(request, code):
    event = Event.objects.published().filter(code=code).first()
    if event:
        response = HttpResponse(event.ics, content_type="text/calendar")
        response["Content-Disposition"] = f"attachment; filename={code}.ics"
        return response
    return HttpResponseNotFound()
