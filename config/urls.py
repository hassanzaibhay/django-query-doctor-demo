from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # query-doctor dashboard MUST be before admin catch-all
    path("admin/query-doctor/", include("query_doctor.urls")),
    path("admin/", admin.site.urls),
    path("", include("shop.urls")),
    path("blog/", include("blog.urls")),
    path("accounts/", include("accounts.urls")),
    path("api/", include("api.urls")),
]
