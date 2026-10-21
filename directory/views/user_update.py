from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from accounts.models import Credential
from core.constants import AREAS
from core.permissions import area_required
from directory.models import Profile
from directory.services import set_areas


@require_POST
@area_required("admin")
def user_update(request, pk):
    # only people of the admin's own company can be edited
    profile = get_object_or_404(Profile, pk=pk, company_id=request.me.company_id)
    if profile.is_owner and not request.me.is_owner:
        raise PermissionDenied
    areas = {a for a in request.POST.getlist("areas") if a in AREAS}
    active = "active" in request.POST
    if profile.id == request.me.id:        # an admin cannot lock themselves out
        active = True
        areas.add("admin")
    new_password = request.POST.get("new_password", "")
    if new_password and len(new_password) < 8:
        messages.error(request, "New password must be at least 8 characters.")
        return redirect("directory:users_list")
    cred = get_object_or_404(Credential, profile_id=profile.id)
    cred.is_active = active
    if new_password:
        cred.password_hash = make_password(new_password)
    cred.save()
    set_areas(profile, areas)
    messages.success(request, "User updated.")
    return redirect("directory:users_list")
