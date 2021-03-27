from django.conf.urls import url

from business import views

urlpatterns = [
    url(r"^tiers/$", views.tiers, name="business_tiers"),
]
