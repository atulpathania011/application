from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import render

from core.permissions import area_required
from core.statement import parse_filters
from purchases.models import Purchase
from sales.models import Invoice

ZERO = Decimal("0")


def _month_totals(model, company_id, start, end):
    """{(year, month): [taxable, gst, total]} for active documents."""
    months = defaultdict(lambda: [ZERO, ZERO, ZERO])
    rows = model.objects.filter(company_id=company_id, status="active", date__range=(start, end))
    for r in rows.values("date", "taxable", "cgst", "sgst", "igst", "total"):
        m = months[(r["date"].year, r["date"].month)]
        m[0] += r["taxable"]
        m[1] += r["cgst"] + r["sgst"] + r["igst"]
        m[2] += r["total"]
    return months


@area_required("reports")
def summary(request):
    f = parse_filters(request.GET)
    if f.problem:
        messages.warning(request, f.problem)
    cid = request.me.company_id
    sales, purchases = _month_totals(Invoice, cid, f.start, f.end), _month_totals(Purchase, cid, f.start, f.end)
    rows = []
    for key in sorted(set(sales) | set(purchases)):
        s, p = sales.get(key, [ZERO] * 3), purchases.get(key, [ZERO] * 3)
        rows.append({"month": date(key[0], key[1], 1), "s_taxable": s[0], "s_gst": s[1], "p_taxable": p[0],
                     "p_gst": p[1], "net": s[1] - p[1]})
    totals = {k: sum((r[k] for r in rows), ZERO) for k in ("s_taxable", "s_gst", "p_taxable", "p_gst", "net")}
    totals["s_total"] = sum((v[2] for v in sales.values()), ZERO)
    totals["p_total"] = sum((v[2] for v in purchases.values()), ZERO)
    return render(request, "reports/summary.html", {
        "f": f, "rows": rows, "totals": totals,
        "can_sales": "sales" in request.me.areas, "can_purchase": "purchase" in request.me.areas})
