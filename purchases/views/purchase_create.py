from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import redirect, render

from core.documents import blank_row, party_values_from_post, rows_from_post
from core.permissions import area_required
from core.redirects import after_save
from purchases.form_context import default_values, purchase_form_context
from purchases.services import create_purchase, duplicate_bill, parse_purchase


@area_required("purchase")
def purchase_create(request):
    company = request.me.company
    if not company.ready:
        messages.error(request, "Add your company name and GSTIN before recording purchases.")
        return redirect("purchases:purchase_list")
    v, rows = default_values(company.state), [blank_row()]
    if request.method == "POST":
        cleaned, errors = parse_purchase(request.POST, company.state)
        if not errors and duplicate_bill(company.id, cleaned):
            errors = ["This supplier's bill number is already recorded."]
        if not errors:
            try:
                p = create_purchase(company, request.me, cleaned, bool(request.POST.get("save_party")))
            except IntegrityError:
                errors = ["Another purchase was saved at the same moment. Click Save purchase again."]
            else:
                messages.success(request, f"Purchase {p.number} saved.")
                return after_save(request, "purchases:purchase_detail", p.pk, "")
        for e in errors:
            messages.error(request, e)
        v, rows = party_values_from_post(request.POST), rows_from_post(request.POST)
    return render(request, "purchases/purchase_form.html",
                  purchase_form_context(request, v=v, rows=rows, company_state=company.state))
