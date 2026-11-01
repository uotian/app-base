from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [path("api/", include("api.urls"))]
# Admin is a Web-only management interface, not part of the desktop bridge.
if not settings.DESKTOP_TOKEN:
    urlpatterns.append(path("admin/", admin.site.urls))
