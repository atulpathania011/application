"""Helpers shared by invoices and purchase bills."""
from .constants import COMPANY_FIELDS, DEFAULT_GST, GST_RATES
from .gst import compute_totals, parse_date, parse_lines, parse_party, plain


def parse_document(post, company_state, party_label):
    """Validate a sales/purchase form. Returns (cleaned, errors)."""
    party, errors = parse_party(post, party_label)
    when = parse_date(post.get("date", ""))
    if when is None:
        errors.append("Enter a valid date.")
    items, item_errors = parse_lines(post)
    errors += item_errors
    if errors:
        return None, errors
    intra = party["state_code"] == company_state
    cleaned = {"date": when, **party, "supply_type": "intra" if intra else "inter", "items": items}
    cleaned.update(compute_totals(items, intra))
    return cleaned, []


def company_snapshot(company):
    """A copy of the company details stored with each document, so later edits never change it."""
    return {k: getattr(company, k) for k in COMPANY_FIELDS}


def apply_cleaned(doc, cleaned):
    for field in ("date", "party_name", "party_gstin", "party_address", "state_code", "supply_type",
                  "taxable", "cgst", "sgst", "igst", "total"):
        setattr(doc, field, cleaned[field])


def make_items(item_model, fk_name, doc, items):
    return [item_model(**{fk_name: doc}, description=i["description"], hsn=i["hsn"], qty=i["qty"],
                       rate=i["rate"], gst_rate=i["gst_rate"], taxable=i["taxable"], tax=i["tax"])
            for i in items]


# ---- form helpers (what the page shows before/after a failed save) ----
GST_OPTIONS = [plain(r) for r in GST_RATES]


def blank_row():
    return {"desc": "", "hsn": "", "qty": "", "rate": "", "gst": DEFAULT_GST}


def rows_from_post(post):
    cols = [post.getlist(k) for k in ("desc", "hsn", "qty", "rate", "gst")]
    rows = [dict(zip(("desc", "hsn", "qty", "rate", "gst"), vals)) for vals in zip(*cols)]
    return rows or [blank_row()]


def rows_from_items(items):
    return [{"desc": i.description, "hsn": i.hsn, "qty": plain(i.qty), "rate": plain(i.rate),
             "gst": plain(i.gst_rate)} for i in items] or [blank_row()]


def party_values_from_post(post):
    return {"party_name": post.get("party_name", ""), "party_gstin": post.get("party_gstin", ""),
            "party_address": post.get("party_address", ""), "state_code": post.get("state_code", ""),
            "date": post.get("date", ""), "bill_number": post.get("bill_number", ""),
            "save_party": bool(post.get("save_party"))}


def party_values_from_doc(doc):
    return {"party_name": doc.party_name, "party_gstin": doc.party_gstin,
            "party_address": doc.party_address, "state_code": doc.state_code,
            "date": doc.date.isoformat(), "bill_number": getattr(doc, "bill_number", ""),
            "save_party": False}
