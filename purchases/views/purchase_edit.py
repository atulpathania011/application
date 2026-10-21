from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from core.documents import party_values_from_doc, party_values_from_post, rows_from_items, rows_from_post
from core.permissions import area_required
from core.redirects import after_save, safe_next
from purchases.form_context import purchase_form_context
from purchases.models import Purchase
from purchases.services import duplicate_bill, parse_purchase, update_purchase


@area_required("purchase")
def purchase_edit(request, pk):
    p = get_object_or_404(Purchase, pk=pk, company_id=request.me.company_id)
    next_url = safe_next(request.POST.get("next") if request.method == "POST" else request.GET.get("next"))
    if p.is_cancelled:
        messages.error(request, "This purchase was cancelled earlier and cannot be edited.")
        return redirect(next_url) if next_url else redirect("purchases:purchase_detail", pk=p.pk)
    company_state = p.company_snapshot.get("state") or request.me.company.state
    v, rows = party_values_from_doc(p), rows_from_items(p.items.all())
    if request.method == "POST":
        cleaned, errors = parse_purchase(request.POST, company_state)
        if not errors and duplicate_bill(p.company_id, cleaned, exclude_pk=p.pk):
            errors = ["This supplier's bill number is already recorded."]
        if not errors:
            update_purchase(p, request.me, cleaned)
            messages.success(request, f"Purchase {p.number} updated.")
            return after_save(request, "purchases:purchase_detail", p.pk, next_url)
        for e in errors:
            messages.error(request, e)
        v, rows = party_values_from_post(request.POST), rows_from_post(request.POST)
    return render(request, "purchases/purchase_form.html", purchase_form_context(
        request, v=v, rows=rows, purchase=p, company_state=company_state, next_url=next_url))
