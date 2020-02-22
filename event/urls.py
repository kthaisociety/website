from django.conf.urls import url

from event import views

urlpatterns = [
    url(r"^event/ics/(?P<code>.*).ics$", views.event_ics, name="events_event_ics"),
    url(r"^event/(?P<code>.*)$", views.event, name="events_event"),
]
