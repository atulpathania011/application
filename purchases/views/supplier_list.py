from django.db.models import Q
from django.shortcuts import render

from core.permissions import area_required
from purchases.models import Supplier


@area_required("purchase")
def supplier_list(request):
    q = request.GET.get("q", "").strip()[:60]
    qs = Supplier.objects.filter(company_id=request.me.company_id)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(gstin__icontains=q) | Q(phone__icontains=q))
    return render(request, "purchases/supplier_list.html", {"rows": qs[:500], "q": q})
