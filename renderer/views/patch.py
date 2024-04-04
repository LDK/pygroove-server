from ..models import Patch, Sample
from ..serializers import PatchSerializer, PatchSerializer
from rest_framework.permissions import AllowAny

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from rest_framework.views import APIView

class PatchViewSet(viewsets.ModelViewSet):
    queryset = Patch.objects.all()
    serializer_class = PatchSerializer

class PatchView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk=None):
        # Check authentication
        # if not request.user.is_authenticated:
        #     return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get patch from database
        try:
            patch = Patch.objects.get(pk=pk)
        except Patch.DoesNotExist:
            return Response({'error': 'Patch not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check to see if the current user is the author of the patch
        # if patch.user != request.user:
        #     return Response({'error': 'Not authorized'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = PatchSerializer(patch)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # updating an existing patch
    def put(self, request, pk=None):
        # Check authentication
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get patch from database
        try:
            patch = Patch.objects.get(pk=pk)
        except Patch.DoesNotExist:
            return Response({'error': 'Patch not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check to see if the current user is the author of the patch
        if patch.user != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_401_UNAUTHORIZED)
    
        # Save patch to database
        patch.name = request.data['name']
        patch.pan = request.data['pan']
        patch.volume = request.data['volume']
        patch.sample = Sample.objects.get(id=request.data['sample']['id'])
        patch.transpose = request.data['transpose']
        patch.rootPitch = request.data['rootPitch']
        patch.pitchShift = request.data['pitchShift']
        patch.reverse = request.data['reverse']
        patch.normalize = request.data['normalize']
        patch.trim = request.data['trim']
        patch.fadeIn = request.data['fadeIn']
        patch.fadeOut = request.data['fadeOut']
        patch.startOffset = request.data['startOffset']
        patch.endOffset = request.data['endOffset']
        patch.playMode = request.data['playMode']
        patch['filters'] = request.data['filters'] if 'filters' in request.data else []
        patch.save()

        # return response
        return Response({'id': patch.id}, status=status.HTTP_200_OK)

    def delete(self, request, pk=None):
        # Check authentication
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get patch from database
        try:
            patch = Patch.objects.get(pk=pk)
        except Patch.DoesNotExist:
            return Response({'error': 'Patch not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check to see if the current user is the author of the patch
        if patch.user != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_401_UNAUTHORIZED)

        # Delete patch from database
        patch.delete()

        print ("DELETED " + str(pk))

        # return response
        return Response({'id': pk}, status=status.HTTP_200_OK)

class CreatePatchView(APIView):
    def post(self, request):
        # Check authentication
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        # Save patch to database
        patch = Patch.objects.create(
            name=request.data['name'],
            user=request.user,
            pan=request.data['pan'],
            volume=request.data['volume'],
            sample=Sample.objects.get(id=request.data['sample']['id']),
            transpose=request.data['transpose'],
            rootPitch=request.data['rootPitch'],
            pitchShift=request.data['pitchShift'],
            reverse=request.data['reverse'],
            normalize=request.data['normalize'],
            trim=request.data['trim'],
            fadeIn=request.data['fadeIn'],
            fadeOut=request.data['fadeOut'],
            startOffset=request.data['startOffset'],
            endOffset=request.data['endOffset'],
            playMode=request.data['playMode'],
            filters=request.data['filters'] if 'filters' in request.data else []
        )

        patch.save()

        # return response
        return Response({'id': patch.id}, status=status.HTTP_201_CREATED)

class RenamePatchView(APIView):
    permission_classes = (AllowAny,)

    def put(self, request, pk=None):
        # Check authentication
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get patch from database
        try:
            patch = Patch.objects.get(pk=pk)
        except Patch.DoesNotExist:
            return Response({'error': 'Patch not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check to see if the current user is the author of the patch
        if patch.user != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_401_UNAUTHORIZED)

        # Save patch to database
        patch.name = request.data['name']
        patch.save()

        # return response
        return Response({'id': patch.id}, status=status.HTTP_200_OK)
