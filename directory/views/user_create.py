from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from core.constants import AREAS
from core.permissions import area_required
from directory.services import UsernameTaken, create_user


@require_POST
@area_required("admin")
def user_create(request):
    username = request.POST.get("username", "").strip().lower()
    full_name = request.POST.get("full_name", "").strip()
    password = request.POST.get("password", "")
    if not username or not full_name or len(password) < 8:
        messages.error(request, "Enter a username, full name and a password of at least 8 characters.")
        return redirect("directory:users_list")
    areas = {a for a in request.POST.getlist("areas") if a in AREAS}
    try:
        create_user(request.me.company, username, full_name, password, areas)
    except UsernameTaken:
        messages.error(request, f"The username '{username}' is already taken. Usernames are unique across all companies.")
    else:
        messages.success(request, f"User '{username}' created.")
    return redirect("directory:users_list")
