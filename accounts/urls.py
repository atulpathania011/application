from django.urls import path

from .views.login import login_view
from .views.logout import logout_view

app_name = "accounts"
urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
]
