from django.conf.urls import url

from business import views

urlpatterns = [url(r"^sponsor/$", views.sponsor, name="business_sponsor")]
