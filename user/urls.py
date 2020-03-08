from django.conf.urls import url
from django.urls import include

from user import views

urlpatterns = [
    url(r"^login/$", views.user_login, name="user_login"),
    url(r"^logout/$", views.user_logout, name="user_logout"),
    url("", include("social_django.urls", namespace="social")),
]
