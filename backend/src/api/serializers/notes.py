from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from apps.notes.models import Note


class NoteInputSerializer(serializers.Serializer[dict[str, str]]):
    text = serializers.CharField(max_length=2000)


class NoteSerializer(serializers.ModelSerializer[Note]):
    class Meta:
        model = Note
        fields = ["id", "text", "created_at"]
        read_only_fields = fields


@extend_schema_serializer(many=False)
class NotePageSerializer(serializers.Serializer[dict[str, object]]):
    count = serializers.IntegerField(min_value=0)
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = NoteSerializer(many=True)
    csrfToken = serializers.CharField()
