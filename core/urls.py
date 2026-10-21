from django.urls import path

from .views.dashboard import dashboard
from .views.home import home
from .views.placeholder import placeholder

app_name = "core"
urlpatterns = [
    path("", home, name="home"),
    path("dashboard/", dashboard, name="dashboard"),
    path("area/<str:key>/", placeholder, name="placeholder"),
]
