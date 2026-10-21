from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.me:
            return redirect("accounts:login")
        return view(request, *args, **kwargs)
    return wrapped


def area_required(*areas):
    """Allow users who have ANY of the listed project areas."""
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.me:
                return redirect("accounts:login")
            if not (request.me.areas & set(areas)):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def owner_required(view):
    """Admin area AND the owner flag - used for adding/disabling companies."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.me:
            return redirect("accounts:login")
        if "admin" not in request.me.areas or not request.me.is_owner:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped
