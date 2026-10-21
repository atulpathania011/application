from django.urls import path

from .views.companies_list import companies_list
from .views.company_create import company_create
from .views.company_details import company_details
from .views.company_toggle import company_toggle
from .views.user_create import user_create
from .views.user_update import user_update
from .views.users_list import users_list

app_name = "directory"
urlpatterns = [
    path("company/", company_details, name="company_details"),
    path("users/", users_list, name="users_list"),
    path("users/new/", user_create, name="user_create"),
    path("users/<int:pk>/", user_update, name="user_update"),
    path("companies/", companies_list, name="companies_list"),
    path("companies/new/", company_create, name="company_create"),
    path("companies/<int:pk>/toggle/", company_toggle, name="company_toggle"),
]
