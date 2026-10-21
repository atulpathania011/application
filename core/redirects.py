"""Remembering which statement a person came from, so they can be sent back to it."""
from urllib.parse import urlencode, urlsplit

from django.shortcuts import redirect
from django.urls import reverse


def safe_next(value):
    """Only our own statement pages are allowed as a 'go back to' address (never another website)."""
    value = (value or "").strip()
    if not value or "\n" in value or "\r" in value or "\\" in value:
        return ""
    parts = urlsplit(value)
    if parts.scheme or parts.netloc or not parts.path.startswith("/statements/"):
        return ""
    return value


def after_save(request, detail_name, pk, next_url):
    """'Save'  -> back to the statement the person came from (or the document page).
    'Save and print' -> the document page, which opens the print window and then returns to the statement."""
    detail = reverse(detail_name, args=[pk])
    if request.POST.get("action") == "save_print":
        params = {"print": "1"}
        if next_url:
            params["next"] = next_url
        return redirect(f"{detail}?{urlencode(params)}")
    return redirect(next_url or detail)
