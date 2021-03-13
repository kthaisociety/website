from django.conf.urls import url

from messaging.api import views

urlpatterns = [url(r"^slack/event/$", views.slack_event, name="slack_event")]
