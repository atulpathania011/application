from django.db import models

from core.models import DocumentBase, LineItemBase, PartyBase


class Supplier(PartyBase):
    """Stored in data/purchases.sqlite3."""


class Purchase(DocumentBase):
    """A purchase bill. number is our own entry number (PUR/2026-27/0001);
    bill_number is the supplier's invoice number; date is the bill date."""
    bill_number = models.CharField(max_length=60)


class PurchaseItem(LineItemBase):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="items")
