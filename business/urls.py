from django.conf.urls import url

from business import views

urlpatterns = [
    url(r"^sponsor/$", views.sponsor, name="business_sponsor"),
    url(r"^jobs/$", views.jobs, name="business_jobs"),
]
