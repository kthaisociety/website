from django.conf.urls import url
from django.urls import include
from django.conf import settings

from user import views

urlpatterns = [
    url(r"^login/$", views.user_login, name="user_login"),
    url(r"^logout/$", views.user_logout, name="user_logout"),
    url(r"^password/$", views.user_password, name="user_password"),
    url(r"^register/$", views.user_register, name="user_register"),
    url(r"^verify/(?P<verification_key>.+)$", views.verify, name="user_verify"),
    url(
        r"^verify-password/(?P<email>.+)/(?P<verification_key>.+)$",
        views.verify_password,
        name="user_verifypassword",
    ),
    url(r"^send-verification/$", views.send_verification, name="user_sendverification"),
    url(r"^dashboard/$", views.dashboard, name="user_dashboard"),
    url(r"^dashboard/resume/$", views.dashboard_resume, name="user_dashboard_resume"),
    url(r"^data/$", views.user_data, name="user_data"),
    url(r"^delete/confirm$", views.user_confirm_delete, name="user_confirm_delete"),
    url(r"^delete/$", views.user_delete, name="user_delete"),
]

if "social_django" in settings.INSTALLED_APPS:
    urlpatterns += [
        url("", include("social_django.urls", namespace="social")),
    ]