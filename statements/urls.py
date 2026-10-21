from django.urls import path

from .views.purchase_statement import purchase_statement
from .views.purchase_statement_csv import purchase_statement_csv
from .views.sales_statement import sales_statement
from .views.sales_statement_csv import sales_statement_csv

app_name = "statements"
urlpatterns = [
    path("sales/", sales_statement, name="sales"),
    path("sales/csv/", sales_statement_csv, name="sales_csv"),
    path("purchases/", purchase_statement, name="purchases"),
    path("purchases/csv/", purchase_statement_csv, name="purchases_csv"),
]
