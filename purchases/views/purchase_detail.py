from django.shortcuts import get_object_or_404, render

from core.permissions import area_required
from core.redirects import safe_next
from directory.models import Profile
from purchases.models import Purchase


@area_required("purchase", "reports")
def purchase_detail(request, pk):
    p = get_object_or_404(Purchase, pk=pk, company_id=request.me.company_id)
    names = dict(Profile.objects.filter(pk__in=[i for i in (p.created_by_id, p.updated_by_id) if i])
                 .values_list("id", "full_name"))
    return render(request, "purchases/purchase_detail.html", {
        "p": p, "items": p.items.all(), "buyer": p.company_snapshot,
        "creator": names.get(p.created_by_id, ""), "editor": names.get(p.updated_by_id, ""),
        "can_edit": "purchase" in request.me.areas,
        "next_url": safe_next(request.GET.get("next")), "autoprint": request.GET.get("print") == "1"})
