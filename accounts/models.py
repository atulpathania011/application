from django.db import models


class Credential(models.Model):
    """Stored in data/credentials.sqlite3. Nothing but the login lives here.

    profile_id points at directory.Profile (which is in a different database file,
    so it is a plain number rather than a ForeignKey).
    """
    username = models.CharField(max_length=60, unique=True)
    password_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)       # "can log in"
    profile_id = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return self.username
