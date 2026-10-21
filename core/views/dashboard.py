from django.shortcuts import render
from django.urls import reverse

from core.constants import AREAS
from core.navigation import area_url
from core.permissions import login_required


@login_required
def dashboard(request):
    mine = request.me.areas
    rows = [{"key": key, **info, "url": area_url(key), "allowed": key in mine} for key, info in AREAS.items()]
    statements = [
        {"title": "Sales statement", "desc": "Every invoice for a period, with totals. Edit and print from here.",
         "url": reverse("statements:sales"), "allowed": bool(mine & {"sales", "reports"})},
        {"title": "Purchase statement", "desc": "Every purchase bill for a period, with totals. Edit and print from here.",
         "url": reverse("statements:purchases"), "allowed": bool(mine & {"purchase", "reports"})},
    ]
    return render(request, "core/dashboard.html", {"rows": rows, "statements": statements, "open_count": len(mine)})
