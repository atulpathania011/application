from django.contrib import messages
from django.shortcuts import render

from core.permissions import area_required
from core.statement import apply_filters, parse_filters, summarize
from sales.models import Invoice

SEARCH = ("number", "party_name", "party_gstin")


@area_required("sales", "reports")
def sales_statement(request):
    f = parse_filters(request.GET)
    if f.problem:
        messages.warning(request, f.problem)
    rows = list(apply_filters(Invoice.objects.filter(company_id=request.me.company_id), f, SEARCH))
    return render(request, "statements/sales_statement.html", {
        "f": f, "rows": rows, "totals": summarize(rows), "can_edit": "sales" in request.me.areas})
