from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from core.parties import is_duplicate, parse_party_form
from core.permissions import area_required
from purchases.models import Supplier


@area_required("purchase")
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk, company_id=request.me.company_id)
    v = {k: getattr(supplier, k) for k in ("name", "gstin", "address", "state", "phone", "email")}
    if request.method == "POST":
        v, errors = parse_party_form(request.POST, "Supplier")
        if not errors and is_duplicate(Supplier, supplier.company_id, v["name"], v["gstin"], exclude_pk=supplier.pk):
            errors.append("A supplier with this name and GSTIN already exists.")
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            for k, val in v.items():
                setattr(supplier, k, val)
            supplier.save()
            messages.success(request, "Supplier saved.")
            return redirect("purchases:supplier_list")
    return render(request, "purchases/supplier_form.html", {"v": v, "supplier": supplier})
