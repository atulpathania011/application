from django.shortcuts import redirect
from django.views.decorators.http import require_POST


@require_POST
def logout_view(request):
    request.session.flush()
    return redirect("accounts:login")
