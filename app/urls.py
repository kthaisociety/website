from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

from app import views
from app.settings import GH_KEY

urlpatterns = [
    url("admin/", admin.site.urls),
    path("api/v1.0/messaging/", include("messaging.api.urls")),
    url(r"^user/", include("user.urls")),
    url(r"^news/", include("news.urls")),
    url(r"^events/", include("event.urls")),
    url(r"^business/", include("business.urls")),
    url(r"^page/", include("page.urls")),
    url(r"^statistics/$", views.statistics, name="app_statistics"),
    url(r"^about/team/(?P<code>.*)?$", views.about_team, name="app_about_team"),
    url(r"^about/contact/", views.about_contact, name="app_about_contact"),
    url(r"^$", views.home, name="app_home"),
    url(r"^files/(?P<file_>.*)$", views.files, name="app_files"),
]

if GH_KEY:
    urlpatterns += [url(r"^deploy/", views.deploy, name="app_deploy")]

handler400 = "app.views.response_400"
handler403 = "app.views.response_403"
handler404 = "app.views.response_404"
handler500 = "app.views.response_500"
