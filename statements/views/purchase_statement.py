from django.contrib import messages
from django.shortcuts import render

from core.permissions import area_required
from core.statement import apply_filters, parse_filters, summarize
from purchases.models import Purchase

SEARCH = ("number", "bill_number", "party_name", "party_gstin")


@area_required("purchase", "reports")
def purchase_statement(request):
    f = parse_filters(request.GET)
    if f.problem:
        messages.warning(request, f.problem)
    rows = list(apply_filters(Purchase.objects.filter(company_id=request.me.company_id), f, SEARCH))
    return render(request, "statements/purchase_statement.html", {
        "f": f, "rows": rows, "totals": summarize(rows), "can_edit": "purchase" in request.me.areas})
