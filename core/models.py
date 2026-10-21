"""Abstract building blocks. Sales and purchases each get their OWN tables (and database file)."""
from django.db import models


class PartyBase(models.Model):
    """A saved customer or supplier."""
    company_id = models.PositiveIntegerField(db_index=True)
    name = models.CharField(max_length=200)
    gstin = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    state = models.CharField(max_length=2)
    phone = models.CharField(max_length=20, blank=True)
    email = models.CharField(max_length=254, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name


class DocumentBase(models.Model):
    """An invoice or a purchase bill. state_code = place of supply (sales) / supplier's state (purchases)."""
    company_id = models.PositiveIntegerField(db_index=True)
    number = models.CharField(max_length=30)
    date = models.DateField()
    party_name = models.CharField(max_length=200)
    party_gstin = models.CharField(max_length=15, blank=True)
    party_address = models.TextField(blank=True)
    state_code = models.CharField(max_length=2)
    supply_type = models.CharField(max_length=5)          # 'intra' (CGST+SGST) or 'inter' (IGST)
    taxable = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    cgst = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    igst = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    status = models.CharField(max_length=10, default="active")   # 'active' or 'cancelled'
    company_snapshot = models.JSONField(default=dict)
    created_by_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by_id = models.PositiveIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["-date", "-id"]
        constraints = [models.UniqueConstraint(fields=["company_id", "number"],
                                               name="%(app_label)s_%(class)s_unique_number")]

    def __str__(self):
        return self.number

    @property
    def gst(self):
        return self.cgst + self.sgst + self.igst

    @property
    def is_cancelled(self):
        return self.status == "cancelled"


class LineItemBase(models.Model):
    description = models.CharField(max_length=200)
    hsn = models.CharField(max_length=8, blank=True)
    qty = models.DecimalField(max_digits=16, decimal_places=3)
    rate = models.DecimalField(max_digits=18, decimal_places=4)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2)
    taxable = models.DecimalField(max_digits=16, decimal_places=2)
    tax = models.DecimalField(max_digits=16, decimal_places=2)

    class Meta:
        abstract = True
        ordering = ["id"]
