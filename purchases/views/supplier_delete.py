from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from core.permissions import area_required
from purchases.models import Supplier


@require_POST
@area_required("purchase")
def supplier_delete(request, pk):
    get_object_or_404(Supplier, pk=pk, company_id=request.me.company_id).delete()
    messages.success(request, "Supplier deleted. Existing purchases are not affected.")
    return redirect("purchases:supplier_list")
