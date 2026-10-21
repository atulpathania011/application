from django.db import models

from core.models import DocumentBase, LineItemBase, PartyBase


class Customer(PartyBase):
    """Stored in data/invoices.sqlite3."""


class Invoice(DocumentBase):
    """A sales (tax) invoice. number looks like INV/2026-27/0001."""


class InvoiceItem(LineItemBase):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
