from core.permissions import area_required
from core.statement import apply_filters, csv_response, parse_filters
from sales.models import Invoice

from .sales_statement import SEARCH


@area_required("sales", "reports")
def sales_statement_csv(request):
    f = parse_filters(request.GET)
    qs = apply_filters(Invoice.objects.filter(company_id=request.me.company_id), f, SEARCH)
    lines = [(r.date.isoformat(), r.number, r.party_name, r.party_gstin, r.taxable, r.cgst, r.sgst, r.igst, r.total)
             for r in qs if not r.is_cancelled]
    return csv_response(f"sales-statement-{f.start}-to-{f.end}.csv",
                        ["Date", "Invoice no", "Customer", "GSTIN", "Taxable", "CGST", "SGST", "IGST", "Total"], lines)
