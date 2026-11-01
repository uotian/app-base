from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

if TYPE_CHECKING:
    from rest_framework.views import APIView


class DesktopAccess(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        token: str = settings.DESKTOP_TOKEN
        return not token or secrets.compare_digest(
            request.headers.get("Authorization", "").encode(), f"Bearer {token}".encode()
        )
