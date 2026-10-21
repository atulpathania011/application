from .gst import financial_year


def next_number(model, company_id, when, word):
    """e.g. INV/2026-27/0001. Numbers run separately for each company and financial year."""
    prefix = f"{word}/{financial_year(when)}/"
    used = model.objects.filter(company_id=company_id, number__startswith=prefix).values_list("number", flat=True)
    last = max((int(n[len(prefix):]) for n in used if n[len(prefix):].isdigit()), default=0)
    return f"{prefix}{last + 1:04d}"
