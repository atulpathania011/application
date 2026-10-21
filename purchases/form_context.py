from datetime import date

from core.constants import STATES
from core.documents import GST_OPTIONS, blank_row
from core.parties import party_choices

from .models import Supplier


def purchase_form_context(request, *, v, rows, purchase=None, company_state, next_url=""):
    return {
        "purchase": purchase, "v": v, "rows": rows, "blank_row": blank_row(), "gst_options": GST_OPTIONS,
        "parties": party_choices(Supplier, request.me.company_id), "company_state": company_state,
        "states": STATES, "next_url": next_url,
    }


def default_values(company_state):
    return {"party_name": "", "party_gstin": "", "party_address": "", "state_code": company_state,
            "date": date.today().isoformat(), "bill_number": "", "save_party": True}
