from django.conf.urls import url

from page import views

urlpatterns = [url(r"^(?P<category>.*)/(?P<code>.*)/$", views.page, name="page_page")]
