from functools import lru_cache

from django.contrib.auth.hashers import check_password, make_password

from directory.models import Profile

from .models import Credential


@lru_cache(maxsize=1)
def _dummy_hash():
    return make_password("not-a-real-password")


def authenticate(username, password):
    """Return the user's Profile if the username/password are right and the account is allowed in."""
    cred = Credential.objects.filter(username=username, is_active=True).first()
    if cred is None:
        check_password(password, _dummy_hash())   # same time taken whether or not the user exists
        return None
    if not check_password(password, cred.password_hash):
        return None
    return Profile.objects.select_related("company").filter(pk=cred.profile_id, company__is_active=True).first()
