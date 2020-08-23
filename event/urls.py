from django.conf.urls import url

from event import views

urlpatterns = [
    url(r"^event/ics/(?P<code>.*).ics$", views.event_ics, name="events_event_ics"),
    url(r"^event/(?P<code>.*)/live$", views.live, name="events_live"),
    url(r"^event/(?P<code>.*)$", views.event, name="events_event"),
    url(
        r"^registration/(?P<registration_id>.*)/url$",
        views.registration_url,
        name="registration_url",
    ),
    url(r"^$", views.events, name="events_events"),
]
