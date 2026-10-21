from django.urls import reverse

AREA_URLS = {
    "sales": ("sales:invoice_list", {}),
    "purchase": ("purchases:purchase_list", {}),
    "returns": ("core:placeholder", {"key": "returns"}),
    "inventory": ("core:placeholder", {"key": "inventory"}),
    "reports": ("reports:summary", {}),
    "admin": ("directory:company_details", {}),
}


def area_url(key):
    name, kwargs = AREA_URLS[key]
    return reverse(name, kwargs=kwargs)
