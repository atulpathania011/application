from accounts.models import Credential
from directory.models import Profile, ProfileArea

from .current_user import CurrentUser


class CurrentUserMiddleware:
    """Sets request.me on every request: who is logged in, for which company, with which areas.

    The user is re-checked each time, so disabling a user or a company takes effect immediately.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.me = None
        pid = request.session.get("pid")
        if pid:
            cred = Credential.objects.filter(profile_id=pid, is_active=True).first()
            profile = (Profile.objects.select_related("company")
                       .filter(pk=pid, company__is_active=True).first()) if cred else None
            if cred and profile:
                areas = frozenset(ProfileArea.objects.filter(profile_id=pid).values_list("area", flat=True))
                request.me = CurrentUser(profile.id, cred.username, profile.full_name,
                                         profile.company, profile.is_owner, areas)
            else:
                request.session.flush()
        return self.get_response(request)
