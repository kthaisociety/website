from django.conf.urls import url

from news import views

urlpatterns = [
    url(r"^(?P<year>.*)/(?P<month>.*)/(?P<day>.*)/(?P<slug>.*)$", views.article, name="news_article"),
]
