from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from api.serializers.notes import NoteInputSerializer, NotePageSerializer, NoteSerializer
from apps.notes.models import Note


@method_decorator(never_cache, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class NotesViewSet(ViewSet):
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[OpenApiParameter("page", int, description="ページ番号（1から）")],
        responses={200: NotePageSerializer},
    )
    def list(self, request: Request) -> Response:
        pagination = PageNumberPagination()
        pagination.page_size = 20
        notes = pagination.paginate_queryset(Note.objects.all(), request, view=self)
        response = pagination.get_paginated_response(NoteSerializer(notes, many=True).data)
        response.data["csrfToken"] = get_token(request._request)
        return response

    @extend_schema(
        request=NoteInputSerializer,
        responses={201: NoteSerializer},
        parameters=[
            OpenApiParameter(
                "X-CSRFToken",
                str,
                OpenApiParameter.HEADER,
                required=True,
                description=("一覧のcsrfToken。同じクライアントのcsrftoken Cookieも送信する。"),
            )
        ],
    )
    def create(self, request: Request) -> Response:
        serializer = NoteInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = Note.objects.create(text=serializer.validated_data["text"])
        return Response(NoteSerializer(note).data, status=201)
