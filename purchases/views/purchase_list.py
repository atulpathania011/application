from django.db.models import Q
from django.shortcuts import render

from core.permissions import area_required
from purchases.models import Purchase


@area_required("purchase")
def purchase_list(request):
    q = request.GET.get("q", "").strip()[:60]
    qs = Purchase.objects.filter(company_id=request.me.company_id)
    if q:
        qs = qs.filter(Q(number__icontains=q) | Q(bill_number__icontains=q)
                       | Q(party_name__icontains=q) | Q(party_gstin__icontains=q))
    return render(request, "purchases/purchase_list.html", {
        "purchases": qs[:100], "q": q, "company_ready": request.me.company.ready})
