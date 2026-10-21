"""GST maths and form checking shared by sales and purchases (all calculated on the server)."""
import re
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .constants import GST_RATES, GSTIN_RE, STATES

TWO = Decimal("0.01")
QTY_STEP = Decimal("0.001")
RATE_STEP = Decimal("0.0001")
MAX_VALUE = Decimal("1000000000")


def money(x):
    return Decimal(x).quantize(TWO, rounding=ROUND_HALF_UP)


def plain(x):
    """Decimal as plain text without trailing zeros: 18.00 -> '18', 0.250 -> '0.25'."""
    return format(Decimal(str(x)).normalize(), "f")


def fy_start_year(d):
    return d.year if d.month >= 4 else d.year - 1


def financial_year(d):
    s = fy_start_year(d)
    return f"{s}-{str(s + 1)[-2:]}"


def fy_bounds(d):
    s = fy_start_year(d)
    return date(s, 4, 1), date(s + 1, 3, 31)


def parse_date(value):
    try:
        return date.fromisoformat((value or "").strip())
    except ValueError:
        return None


def valid_phone(p):
    return len(p) <= 20 and all(ch in "0123456789+-() " for ch in p)


def valid_email(e):
    return "@" in e and " " not in e and len(e) <= 254


def check_gstin(gstin, state):
    if not gstin:
        return None
    if not GSTIN_RE.match(gstin):
        return "GSTIN is not in a valid format."
    if state in STATES and gstin[:2] != state:
        return "GSTIN state code does not match the selected state."
    return None


def parse_party(post, label):
    """label is 'Customer' or 'Supplier'. Reads party_name/party_gstin/party_address/state_code."""
    v = {
        "party_name": post.get("party_name", "").strip(),
        "party_gstin": post.get("party_gstin", "").strip().upper(),
        "party_address": post.get("party_address", "").strip(),
        "state_code": post.get("state_code", ""),
    }
    errors = []
    if not v["party_name"]:
        errors.append(f"Enter the {label.lower()} name.")
    if v["state_code"] not in STATES:
        errors.append("Choose the state.")
    err = check_gstin(v["party_gstin"], v["state_code"])
    if err:
        errors.append(f"{label} {err[0].lower()}{err[1:]}")
    return v, errors


def parse_lines(post):
    """Return (items, errors) from the repeated desc/hsn/qty/rate/gst form fields."""
    items, errors = [], []
    cols = [post.getlist(k) for k in ("desc", "hsn", "qty", "rate", "gst")]
    for desc, hsn, qty_s, rate_s, gst_s in zip(*cols):
        desc, hsn = desc.strip(), hsn.strip()
        if not (desc or qty_s.strip() or rate_s.strip()):
            continue  # ignore completely blank rows
        try:
            qty, rate, gst = Decimal(qty_s), Decimal(rate_s), Decimal(gst_s)
            ok = (bool(desc) and qty.is_finite() and rate.is_finite()
                  and 0 < qty <= MAX_VALUE and 0 <= rate <= MAX_VALUE and gst in GST_RATES)
            if ok:
                qty = qty.quantize(QTY_STEP, rounding=ROUND_HALF_UP)
                rate = rate.quantize(RATE_STEP, rounding=ROUND_HALF_UP)
        except InvalidOperation:
            ok = False
        if not ok:
            errors.append("Each item needs a description, a quantity above 0, a rate and a GST %.")
            break
        if hsn and not re.fullmatch(r"\d{4,8}", hsn):
            errors.append("HSN/SAC must be 4 to 8 digits.")
            break
        taxable = money(qty * rate)
        items.append({"description": desc, "hsn": hsn, "qty": qty, "rate": rate, "gst_rate": gst,
                      "taxable": taxable, "tax": money(taxable * gst / 100)})
    if not items and not errors:
        errors.append("Add at least one item.")
    return items, errors


def compute_totals(items, intra):
    """Same state -> CGST + SGST; different state -> IGST."""
    taxable = sum((i["taxable"] for i in items), Decimal("0"))
    tax = sum((i["tax"] for i in items), Decimal("0"))
    cgst = money(tax / 2) if intra else Decimal("0")
    sgst = tax - cgst if intra else Decimal("0")
    igst = Decimal("0") if intra else tax
    return {"taxable": taxable, "cgst": cgst, "sgst": sgst, "igst": igst, "total": taxable + tax}
