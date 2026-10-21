"""Period filters, totals and CSV export shared by the sales/purchase statements and reports."""
import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Q
from django.http import HttpResponse

from .gst import fy_bounds, parse_date


@dataclass
class Filters:
    start: date
    end: date
    status: str = "all"
    q: str = ""
    problem: str = ""


def parse_filters(params):
    """from / to / status / q from the query string; defaults to the current financial year."""
    default_start, default_end = fy_bounds(date.today())
    start, end, problem = parse_date(params.get("from")), parse_date(params.get("to")), ""
    if (params.get("from") and start is None) or (params.get("to") and end is None):
        problem = "One of the dates was not valid, so the current financial year is shown."
        start = end = None
    start, end = start or default_start, end or default_end
    if start > end:
        problem = "'From' was after 'To', so the dates were swapped."
        start, end = end, start
    status = params.get("status", "all")
    return Filters(start, end, status if status in ("all", "active", "cancelled") else "all",
                   params.get("q", "").strip()[:60], problem)


def apply_filters(qs, f, search_fields):
    qs = qs.filter(date__range=(f.start, f.end))
    if f.status != "all":
        qs = qs.filter(status=f.status)
    if f.q:
        cond = Q()
        for field in search_fields:
            cond |= Q(**{f"{field}__icontains": f.q})
        qs = qs.filter(cond)
    return qs.order_by("date", "id")


def summarize(rows):
    """Totals over ACTIVE rows only (cancelled documents are shown but not counted)."""
    t = {k: Decimal("0") for k in ("taxable", "cgst", "sgst", "igst", "total")}
    t["count"] = t["cancelled"] = 0
    for r in rows:
        if r.status == "cancelled":
            t["cancelled"] += 1
            continue
        t["count"] += 1
        for k in ("taxable", "cgst", "sgst", "igst", "total"):
            t[k] += getattr(r, k)
    t["gst"] = t["cgst"] + t["sgst"] + t["igst"]
    return t


def _safe(value):
    """Stop spreadsheet programs from running text that starts with = + - @ as a formula."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def csv_response(filename, header, lines):
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    resp.write("\ufeff")  # lets Excel read the file as UTF-8
    writer = csv.writer(resp)
    writer.writerow(header)
    for line in lines:
        writer.writerow([_safe(x) for x in line])
    return resp
