from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from core.constants import AREAS, STATES
from core.gst import check_gstin
from core.permissions import owner_required
from directory.models import Company
from directory.services import UsernameTaken, create_user


@require_POST
@owner_required
def company_create(request):
    p = request.POST
    name, address, state = p.get("name", "").strip(), p.get("address", "").strip(), p.get("state", "")
    gstin = p.get("gstin", "").strip().upper()
    username = p.get("admin_username", "").strip().lower()
    full_name, password = p.get("admin_name", "").strip(), p.get("admin_password", "")
    errors = []
    if not name:
        errors.append("Enter the company name.")
    if not gstin:
        errors.append("Enter the company GSTIN.")
    if state not in STATES:
        errors.append("Choose the company's state.")
    err = check_gstin(gstin, state)
    if err:
        errors.append(err)
    if not username or not full_name or len(password) < 8:
        errors.append("Enter the company admin's username, name and a password of at least 8 characters.")
    if not errors:
        company = Company.objects.create(name=name, gstin=gstin, address=address, state=state)
        try:
            create_user(company, username, full_name, password, set(AREAS))
        except UsernameTaken:
            company.delete()
            errors.append(f"The username '{username}' is already taken.")
        else:
            messages.success(request, f"Company '{name}' created. Its admin can now log in as '{username}'.")
    for e in errors:
        messages.error(request, e)
    return redirect("directory:companies_list")
