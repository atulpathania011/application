from django.http import HttpResponseServerError
from django.shortcuts import render


def _page(request, status, title, text):
    return render(request, "error.html", {"title": title, "text": text}, status=status)


def bad_request(request, exception=None):
    return _page(request, 400, "Request could not be understood", "Go back and try again.")


def forbidden(request, exception=None):
    return _page(request, 403, "You don't have access to this area",
                 "Ask your administrator to add it to your account.")


def not_found(request, exception=None):
    return _page(request, 404, "Page not found", "Check the address or go back to your dashboard.")


def csrf_failure(request, reason=""):
    return _page(request, 403, "Request could not be verified", "Reload the page and try again.")


def server_error(request):
    return HttpResponseServerError("<h1>Something went wrong</h1><p>Please try again, or contact your administrator.</p>")
