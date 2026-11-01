from rest_framework import serializers


class GreetingSerializer(serializers.Serializer[dict[str, str]]):
    message = serializers.CharField()
