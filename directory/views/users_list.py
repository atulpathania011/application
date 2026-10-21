from django.shortcuts import render

from accounts.models import Credential
from core.permissions import area_required
from directory.models import Profile, ProfileArea


@area_required("admin")
def users_list(request):
    profiles = list(Profile.objects.filter(company_id=request.me.company_id).order_by("full_name"))
    ids = [p.id for p in profiles]
    creds = {c.profile_id: c for c in Credential.objects.filter(profile_id__in=ids)}
    areas = {}
    for pa in ProfileArea.objects.filter(profile_id__in=ids):
        areas.setdefault(pa.profile_id, set()).add(pa.area)
    rows = [{"id": p.id, "full_name": p.full_name, "is_owner": p.is_owner,
             "username": creds[p.id].username if p.id in creds else "(no login)",
             "active": creds[p.id].is_active if p.id in creds else False,
             "areas": areas.get(p.id, set())} for p in profiles]
    return render(request, "directory/users_list.html", {"rows": rows})
