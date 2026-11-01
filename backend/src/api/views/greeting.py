from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.greeting import GreetingSerializer


class GreetingView(APIView):
    serializer_class = GreetingSerializer

    def get(self, request: Request) -> Response:
        serializer = GreetingSerializer({"message": "Django + DRF が動いています"})
        return Response(serializer.data)
