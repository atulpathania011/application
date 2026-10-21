from django.urls import include, path

urlpatterns = [
    path("", include("core.urls")),
    path("", include("accounts.urls")),
    path("manage/", include("directory.urls")),
    path("statements/", include("statements.urls")),
    path("sales/", include("sales.urls")),
    path("purchases/", include("purchases.urls")),
    path("reports/", include("reports.urls")),
]

handler400 = "core.views.errors.bad_request"
handler403 = "core.views.errors.forbidden"
handler404 = "core.views.errors.not_found"
handler500 = "core.views.errors.server_error"
