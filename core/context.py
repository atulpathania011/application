from .constants import AREAS, STATES


def globals(request):
    return {"me": getattr(request, "me", None), "AREAS": AREAS, "STATES": STATES}
