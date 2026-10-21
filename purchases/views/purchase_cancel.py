from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.permissions import area_required
from purchases.models import Purchase


@require_POST
@area_required("purchase")
def purchase_cancel(request, pk):
    p = get_object_or_404(Purchase, pk=pk, company_id=request.me.company_id)
    if not p.is_cancelled:
        p.status = "cancelled"
        p.updated_by_id, p.updated_at = request.me.id, timezone.now()
        p.save()
        messages.success(request, f"Purchase {p.number} cancelled.")
    return redirect("purchases:purchase_detail", pk=p.pk)
