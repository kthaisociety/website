from django.conf.urls import url

from event import views

urlpatterns = [
    url(r"^event/ics/(?P<code>.*).ics$", views.event_ics, name="events_event_ics"),
    url(
        r"^event/(?P<code>.*)/poster.png$",
        views.event_poster,
        name="events_event_poster",
    ),
    url(r"^event/(?P<code>.*)/live$", views.live, name="events_live"),
    url(
        r"^event/(?P<event_id>.*)/register$",
        views.checkin_event_register,
        name="events_checkin_event_register",
    ),
    url(
        r"^event/(?P<event_id>.*)/download$",
        views.checkin_event_download,
        name="events_checkin_event_download",
    ),
    url(r"^event/(?P<code>.*)$", views.event, name="events_event"),
    url(
        r"^registration/(?P<registration_id>.*)/url$",
        views.registration_url,
        name="registration_url",
    ),
    url(r"^$", views.events, name="events_events"),
    url(r"^checkin$", views.checkin_events, name="events_checkin_events"),
    url(
        r"^checkin/attend/(?P<registration_id>.*)$",
        views.checkin_event_attend,
        name="events_checkin_event_attend",
    ),
    url(
        r"^checkin/(?P<code>.*)/qr$",
        views.checkin_event_qr,
        name="events_checkin_event_qr",
    ),
    url(r"^checkin/(?P<code>.*)$", views.checkin_event, name="events_checkin_event"),
]
