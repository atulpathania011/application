from django.urls import path

from .views.summary import summary

app_name = "reports"
urlpatterns = [path("", summary, name="summary")]
