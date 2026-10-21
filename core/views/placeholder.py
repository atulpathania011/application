from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, render

from core.constants import AREAS


def placeholder(request, key):
    """Pages for areas that are not built yet (GST returns, Inventory)."""
    if key not in ("returns", "inventory"):
        raise Http404
    if not request.me:
        return redirect("accounts:login")
    if key not in request.me.areas:
        raise PermissionDenied
    return render(request, "core/placeholder.html", {"area": AREAS[key]})
