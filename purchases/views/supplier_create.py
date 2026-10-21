from django.contrib import messages
from django.shortcuts import redirect, render

from core.parties import is_duplicate, parse_party_form
from core.permissions import area_required
from purchases.models import Supplier


@area_required("purchase")
def supplier_create(request):
    company = request.me.company
    v = {"name": "", "gstin": "", "address": "", "state": company.state, "phone": "", "email": ""}
    if request.method == "POST":
        v, errors = parse_party_form(request.POST, "Supplier")
        if not errors and is_duplicate(Supplier, company.id, v["name"], v["gstin"]):
            errors.append("A supplier with this name and GSTIN already exists.")
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            Supplier.objects.create(company_id=company.id, **v)
            messages.success(request, "Supplier saved.")
            return redirect("purchases:supplier_list")
    return render(request, "purchases/supplier_form.html", {"v": v, "supplier": None})
