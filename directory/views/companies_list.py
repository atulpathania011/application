from django.shortcuts import render

from core.permissions import owner_required
from directory.models import Company, Profile
from purchases.models import Purchase
from sales.models import Invoice


@owner_required
def companies_list(request):
    rows = [{"company": c, "n_users": Profile.objects.filter(company=c).count(),
             "n_invoices": Invoice.objects.filter(company_id=c.id).count(),
             "n_purchases": Purchase.objects.filter(company_id=c.id).count()}
            for c in Company.objects.order_by("id")]
    return render(request, "directory/companies_list.html", {"rows": rows})
