from django.conf import settings
from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import SimpleRouter

from api.views.greeting import GreetingView
from api.views.notes import NotesViewSet

urlpatterns: list[URLPattern | URLResolver] = [
    path("greeting/", GreetingView.as_view(), name="greeting")
]
if not settings.DESKTOP_TOKEN:
    router = SimpleRouter()
    router.register("notes", NotesViewSet, basename="notes")
    urlpatterns += [
        path("", include(router.urls)),
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]
