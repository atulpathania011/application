from django.contrib import messages
from django.shortcuts import redirect, render

from accounts import lockout
from accounts.services import authenticate


def login_view(request):
    if request.me:
        return redirect("core:dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        password = request.POST.get("password", "")
        ip = request.META.get("REMOTE_ADDR", "")
        if lockout.is_locked(username, ip):
            messages.error(request, "Too many failed attempts. Try again in 5 minutes.")
            return render(request, "accounts/login.html", status=429)
        profile = authenticate(username, password)
        if profile:
            lockout.clear(username, ip)
            request.session.flush()                 # brand-new session on every login
            request.session["pid"] = profile.id
            return redirect("core:dashboard")       # always start on the home page
        lockout.record_failure(username, ip)
        messages.error(request, "Username or password is incorrect, or the account is disabled.")
    return render(request, "accounts/login.html")
