import io
from renderer.groove import renderJSON, renderPatternPreview
from ..models import Pattern
from ..serializers import PatternSerializer
from rest_framework.permissions import AllowAny

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from django.http import FileResponse
from rest_framework.views import APIView

class PatternViewSet(viewsets.ModelViewSet):
    queryset = Pattern.objects.all()
    serializer_class = PatternSerializer

class PreviewPatternView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        # Call renderJSON and get MP3 data as bytes
        mp3_data = renderPatternPreview(request.data)

        # Create a FileResponse with MP3 data
        response = FileResponse(io.BytesIO(mp3_data), as_attachment=True, filename='rendered_audio.mp3')
        response['Content-Type'] = 'audio/mpeg'

        return response

class PianoPatternView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        # Call renderJSON and get MP3 data as bytes
        mp3_data = renderJSON(request.data)

        # Create a FileResponse with MP3 data
        response = FileResponse(io.BytesIO(mp3_data), as_attachment=True, filename='rendered_audio.mp3')
        response['Content-Type'] = 'audio/mpeg'

        return response
