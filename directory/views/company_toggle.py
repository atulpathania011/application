from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from core.permissions import owner_required
from directory.models import Company


@require_POST
@owner_required
def company_toggle(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if company.id == request.me.company_id:
        messages.error(request, "You cannot deactivate your own company.")
    else:
        company.is_active = not company.is_active
        company.save()
        messages.success(request, "Company status changed. Its users are logged out or allowed back in immediately.")
    return redirect("directory:companies_list")
