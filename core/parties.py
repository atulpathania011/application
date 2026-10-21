"""Customer / supplier master helpers (same rules for both)."""
from .constants import STATES
from .gst import check_gstin, valid_email, valid_phone


def parse_party_form(post, label):
    v = {k: post.get(k, "").strip() for k in ("name", "gstin", "address", "state", "phone", "email")}
    v["gstin"] = v["gstin"].upper()
    errors = []
    if not v["name"]:
        errors.append(f"Enter the {label.lower()} name.")
    if v["state"] not in STATES:
        errors.append(f"Choose the {label.lower()}'s state.")
    err = check_gstin(v["gstin"], v["state"])
    if err:
        errors.append(err)
    if v["phone"] and not valid_phone(v["phone"]):
        errors.append("Phone number can contain only digits, spaces, + - ( ).")
    if v["email"] and not valid_email(v["email"]):
        errors.append("Enter a valid email address.")
    return v, errors


def is_duplicate(model, company_id, name, gstin, exclude_pk=None):
    qs = model.objects.filter(company_id=company_id, name__iexact=name, gstin=gstin)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def party_choices(model, company_id):
    """Saved parties shaped for the document form's auto-fill."""
    out = []
    for p in model.objects.filter(company_id=company_id).order_by("name"):
        label = f"{p.name} ({p.gstin})" if p.gstin else f"{p.name} (unregistered)"
        out.append({"label": label, "name": p.name, "gstin": p.gstin, "address": p.address, "state": p.state})
    return out


def save_party_if_new(model, company_id, cleaned):
    if is_duplicate(model, company_id, cleaned["party_name"], cleaned["party_gstin"]):
        return
    model.objects.create(company_id=company_id, name=cleaned["party_name"], gstin=cleaned["party_gstin"],
                         address=cleaned["party_address"], state=cleaned["state_code"])
