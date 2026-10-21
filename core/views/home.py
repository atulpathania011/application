from django.shortcuts import redirect


def home(request):
    """Everyone starts on the home page (dashboard) after logging in."""
    return redirect("core:dashboard" if request.me else "accounts:login")
