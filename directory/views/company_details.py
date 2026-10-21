from django.contrib import messages
from django.shortcuts import redirect, render

from core.constants import COMPANY_FIELDS, STATES
from core.gst import check_gstin, valid_email, valid_phone
from core.permissions import area_required


@area_required("admin")
def company_details(request):
    company = request.me.company
    v = {k: getattr(company, k) for k in COMPANY_FIELDS}
    if request.method == "POST":
        v = {k: request.POST.get(k, "").strip() for k in COMPANY_FIELDS}
        v["gstin"] = v["gstin"].upper()
        errors = []
        if not v["name"]:
            errors.append("Enter your company name.")
        if not v["gstin"]:
            errors.append("Enter your GSTIN.")
        if v["state"] not in STATES:
            errors.append("Choose your state.")
        err = check_gstin(v["gstin"], v["state"])
        if err:
            errors.append(err)
        if v["phone"] and not valid_phone(v["phone"]):
            errors.append("Phone number can contain only digits, spaces, + - ( ).")
        if v["email"] and not valid_email(v["email"]):
            errors.append("Enter a valid email address.")
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            for k, val in v.items():
                setattr(company, k, val)
            company.save()
            messages.success(request, "Company details saved. New invoices and purchases will use them.")
            return redirect("directory:company_details")
    return render(request, "directory/company_details.html", {"v": v})
