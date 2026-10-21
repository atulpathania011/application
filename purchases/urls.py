from django.urls import path

from .views.purchase_create import purchase_create
from .views.purchase_detail import purchase_detail
from .views.purchase_edit import purchase_edit
from .views.purchase_list import purchase_list
from .views.supplier_create import supplier_create
from .views.supplier_delete import supplier_delete
from .views.supplier_edit import supplier_edit
from .views.supplier_list import supplier_list

app_name = "purchases"
urlpatterns = [
    path("", purchase_list, name="purchase_list"),
    path("new/", purchase_create, name="purchase_create"),
    path("suppliers/", supplier_list, name="supplier_list"),
    path("suppliers/new/", supplier_create, name="supplier_create"),
    path("suppliers/<int:pk>/", supplier_edit, name="supplier_edit"),
    path("suppliers/<int:pk>/delete/", supplier_delete, name="supplier_delete"),
    path("<int:pk>/", purchase_detail, name="purchase_detail"),
    path("<int:pk>/edit/", purchase_edit, name="purchase_edit"),
]
