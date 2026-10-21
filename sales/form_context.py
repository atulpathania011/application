from datetime import date

from core.constants import STATES
from core.documents import GST_OPTIONS, blank_row
from core.parties import party_choices

from .models import Customer


def invoice_form_context(request, *, v, rows, invoice=None, company_state, next_url=""):
    return {
        "invoice": invoice, "v": v, "rows": rows, "blank_row": blank_row(), "gst_options": GST_OPTIONS,
        "parties": party_choices(Customer, request.me.company_id), "company_state": company_state,
        "states": STATES, "next_url": next_url,
    }


def default_values(company_state):
    return {"party_name": "", "party_gstin": "", "party_address": "", "state_code": company_state,
            "date": date.today().isoformat(), "save_party": True}
