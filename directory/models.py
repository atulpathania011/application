from django.db import models


class Company(models.Model):
    """Stored in data/users.sqlite3."""
    name = models.CharField(max_length=200, blank=True)
    gstin = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    state = models.CharField(max_length=2, default="09")
    phone = models.CharField(max_length=20, blank=True)
    email = models.CharField(max_length=254, blank=True)
    bank = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name or f"Company {self.pk}"

    @property
    def ready(self):
        """Invoices and purchases need at least a name and a GSTIN."""
        return bool(self.name and self.gstin)


class Profile(models.Model):
    """A person: name, company and owner flag. Their password is NOT here (see accounts.Credential)."""
    full_name = models.CharField(max_length=150)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="profiles")
    is_owner = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name


class ProfileArea(models.Model):
    """One row per project area a person is allowed to open."""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="areas")
    area = models.CharField(max_length=20)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["profile", "area"], name="unique_profile_area")]
