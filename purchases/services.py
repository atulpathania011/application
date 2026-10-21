from django.db import transaction
from django.utils import timezone

from core.documents import apply_cleaned, company_snapshot, make_items, parse_document
from core.numbering import next_number
from core.parties import save_party_if_new

from .models import Purchase, PurchaseItem, Supplier


def parse_purchase(post, company_state):
    """Like an invoice form, plus the supplier's own bill number."""
    cleaned, errors = parse_document(post, company_state, "Supplier")
    bill_number = post.get("bill_number", "").strip()
    if not bill_number:
        errors = errors + ["Enter the supplier's bill number."]
    elif len(bill_number) > 60:
        errors = errors + ["The supplier's bill number is too long (60 characters at most)."]
    if errors:
        return None, errors
    cleaned["bill_number"] = bill_number
    return cleaned, []


def duplicate_bill(company_id, cleaned, exclude_pk=None):
    """The same supplier cannot have the same bill number recorded twice (cancelled bills are ignored)."""
    qs = Purchase.objects.filter(company_id=company_id, bill_number__iexact=cleaned["bill_number"],
                                 party_gstin=cleaned["party_gstin"], status="active")
    if not cleaned["party_gstin"]:
        qs = qs.filter(party_name__iexact=cleaned["party_name"])
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def create_purchase(company, me, cleaned, save_supplier):
    with transaction.atomic(using="purchases"):
        p = Purchase(company_id=company.id, company_snapshot=company_snapshot(company), created_by_id=me.id,
                     number=next_number(Purchase, company.id, cleaned["date"], "PUR"),
                     bill_number=cleaned["bill_number"])
        apply_cleaned(p, cleaned)
        p.save()
        PurchaseItem.objects.bulk_create(make_items(PurchaseItem, "purchase", p, cleaned["items"]))
        if save_supplier:
            save_party_if_new(Supplier, company.id, cleaned)
    return p


def update_purchase(p, me, cleaned):
    with transaction.atomic(using="purchases"):
        apply_cleaned(p, cleaned)
        p.bill_number = cleaned["bill_number"]
        p.updated_by_id = me.id
        p.updated_at = timezone.now()
        p.save()
        p.items.all().delete()
        PurchaseItem.objects.bulk_create(make_items(PurchaseItem, "purchase", p, cleaned["items"]))
    return p
