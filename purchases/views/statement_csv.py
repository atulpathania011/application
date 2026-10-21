from core.permissions import area_required
from core.statement import apply_filters, csv_response, parse_filters
from purchases.models import Purchase

from .statement import SEARCH


@area_required("purchase", "reports")
def statement_csv(request):
    f = parse_filters(request.GET)
    qs = apply_filters(Purchase.objects.filter(company_id=request.me.company_id), f, SEARCH)
    lines = [(r.date.isoformat(), r.number, r.bill_number, r.party_name, r.party_gstin, r.taxable, r.cgst,
              r.sgst, r.igst, r.total, r.status) for r in qs]
    return csv_response(f"purchase-statement-{f.start}-to-{f.end}.csv",
                        ["Bill date", "Entry no", "Supplier bill no", "Supplier", "GSTIN", "Taxable", "CGST",
                         "SGST", "IGST", "Total", "Status"], lines)
