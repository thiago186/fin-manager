from rest_framework.response import Response
from rest_framework.views import APIView


class RootView(APIView):
    """Simple API view to return a hello message."""

    def get(self, request):
        return Response({"message": "Hello world"})
