from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from studiopilates.core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("studiopilates.core.urls")),
    path("login/", core_views.login_view, name="login"),
    path("logout/", core_views.logout_view, name="logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
