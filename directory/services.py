from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction

from accounts.models import Credential

from .models import Profile, ProfileArea


class UsernameTaken(Exception):
    pass


def area_set(profile_id):
    return set(ProfileArea.objects.filter(profile_id=profile_id).values_list("area", flat=True))


def set_areas(profile, areas):
    with transaction.atomic(using="default"):
        ProfileArea.objects.filter(profile=profile).delete()
        ProfileArea.objects.bulk_create([ProfileArea(profile=profile, area=a) for a in sorted(areas)])


def create_user(company, username, full_name, password, areas, is_owner=False):
    """Profile goes to users.sqlite3 and the login to credentials.sqlite3 (two files, so two steps)."""
    if Credential.objects.filter(username=username).exists():
        raise UsernameTaken(username)
    profile = Profile.objects.create(company=company, full_name=full_name, is_owner=is_owner)
    set_areas(profile, areas)
    try:
        Credential.objects.create(username=username, password_hash=make_password(password), profile_id=profile.id)
    except IntegrityError:
        profile.delete()          # undo the first step
        raise UsernameTaken(username)
    return profile
