from django.conf.urls import url
from django.contrib import admin
from django.urls import include

from app import views
from app.settings import GH_KEY

urlpatterns = [
    url("admin/", admin.site.urls),
    url(r"^user/", include("user.urls")),
    url(r"^$", views.home, name="app_home"),
    url(r"^files/(?P<file_>.*)$", views.files, name="app_files"),
]

if GH_KEY:
    urlpatterns += [url(r"^deploy/", views.deploy, name="app_deploy")]

handler400 = "app.views.response_400"
handler403 = "app.views.response_403"
handler404 = "app.views.response_404"
handler500 = "app.views.response_500"
