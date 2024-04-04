
import base64
from io import BytesIO
import io
from os import curdir, rename
from django.http import FileResponse, HttpResponse
from rest_framework.permissions import AllowAny

from renderer.waveform import Waveform
from renderer.serializers import SampleSerializer, TrackSerializer
from django.contrib.auth import authenticate
from renderer.models import Sample, Track
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from os.path import join as pjoin

from django.conf import settings

from renderer.sample_process import SampleProcess
from renderer.sample_data import SampleData

class SampleViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({
          'username': request.user.username,
          'id': request.user.id,
          'email': request.user.email,
        })

class SampleListSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        output = []

        for sample in queryset:
            serializer = self.get_serializer(sample)
            waveform_image = sample.waveform

            sample_output = {
                'id': serializer.data['id'],
                'filename': serializer.data['filename'],
                'display': serializer.data['display'],
                'frames': serializer.data['frames'],
                'waveform': None,
            }

            if waveform_image.name:  # Check if the image field has a file associated with it
                try:
                    # Construct the URL for the waveform image
                    waveform_url = (request.build_absolute_uri(settings.STATIC_URL) + waveform_image.name).replace('/./waveform', '')
                    sample_output['waveform'] = waveform_url
                except IOError:
                    # Handle the case where the image file does not exist or cannot be opened
                    print("Error opening waveform image for sample id:", sample.id)
                    sample_output['waveform'] = None

            output.append(sample_output)

        return Response(output)

def saveSampleImage(data):
    fName = data['filename']
    fLoc = pjoin("./audio", fName)
    imgLoc = pjoin("./waveform", fName.replace('.wav','.png'))
    waveImg = Waveform(fLoc).save()

    rename(waveImg,imgLoc)
    return { "location": imgLoc, "image": imgLoc }

class CreateSampleView(APIView):
    permission_classes = (AllowAny,)
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer

    def post(self, request, *args, **kwargs):
        serializer = SampleSerializer(data=request.data)

        if serializer.is_valid():
            imgData = saveSampleImage(request.data)
            serializer.save(waveform=imgData['image'])
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SampleView(APIView):
    permission_classes = (AllowAny,)
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer

    def get(self, request, pk=None):
        sample = Sample.objects.get(pk=pk)
        serializer = SampleSerializer(sample)
        waveform_image = sample.waveform

        output = {
            'id': serializer.data['id'],
            'filename': serializer.data['filename'],
            'display': serializer.data['display'],
            'waveform': None,
        }

        if waveform_image.name:  # Check if the image field has a file associated with it
            try:
                with waveform_image.open('rb') as image_file:
                    base64_encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                    output['waveform'] = base64_encoded_image
            except IOError:
                # Handle the case where the image file does not exist or cannot be opened
                print("Error opening waveform image for sample id:", pk)
                output['waveform'] = None
        
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, pk=None):
        sample = Sample.objects.get(pk=pk)
        serializer = SampleSerializer(sample, data=request.data)
        if serializer.is_valid():
            imgData = saveSampleImage(request.data)
            serializer.save(waveform=imgData['image'])
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SampleImageView(APIView):
    permission_classes = (AllowAny,)
    queryset = Track.objects.all()
    serializer_class = SampleSerializer

    def get(self, request, pk=None):
        sample = Sample.objects.get(pk=pk)
        serializer = SampleSerializer(sample)
        fLoc = pjoin("./audio", sample.filename)

        reverse:bool = (request.GET.get('rv', False) in ['true', 'True', True])
        trim:bool = (request.GET.get('tr', False) in ['true', 'True', True])
        normalize:bool = (request.GET.get('nm', False) in ['true', 'True', True])

        waveform_image = Waveform(fLoc, {
            'normalize': normalize,
            'trim': trim,
            'reverse': reverse,
        }).image()

        if waveform_image:
            try:
                # Create a buffer to hold the image data
                buffer = BytesIO()
                # Save the image to the buffer
                waveform_image.save(buffer, format='PNG')
                buffer.seek(0)

                # Create a HttpResponse with the PNG data
                response = HttpResponse(buffer, content_type='image/png')
                return response

            except IOError:
                # Handle the case where the image file does not exist or cannot be opened
                print("Error opening waveform image for sample id:", pk)
                return Response(None, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_200_OK)

class SampleAudioView(APIView):
    permission_classes = (AllowAny,)
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer

    def get(self, request, pk=None):
        sample = Sample.objects.get(pk=pk)
        fLoc = pjoin("./audio", sample.filename)

        reverse:bool = (request.GET.get('rv', False) in ['true', 'True', True])
        trim:bool = (request.GET.get('tr', False) in ['true', 'True', True])
        normalize:bool = (request.GET.get('nm', False) in ['true', 'True', True])
        transpose:int = int(request.GET.get('ts', 0))
        pitchShift:int = int(request.GET.get('ps', 0))
        pan:int = int(request.GET.get('pn', 0))
        volume:float = float(request.GET.get('vl', 0))

        filter1On:bool = (request.GET.get('f1', False) in ['true', 'True', True])
        filter1Type:str = request.GET.get('ft1', 'lowpass')
        fq1:float = float(request.GET.get('fq1', 0))
        filter1Freq:float = float(fq1)
        filter1Order:int = int(request.GET.get('or1', 0))

        filter2On:bool = (request.GET.get('f2', False) in ['true', 'True', True])
        filter2Type:str = request.GET.get('ft2', 'lowpass')
        fq2:float = float(request.GET.get('fq2', 0))
        filter2Freq:float = float(fq2)
        filter2Order:int = int(request.GET.get('or2', 0))
        
        sampleStart = request.GET.get('sst', 0)
        sampleEnd = request.GET.get('sen', 0)

        frames:int = sample.frames

        fadeIn = request.GET.get('fi', 0)
        fadeOut = request.GET.get('fo', 0)

        processed = SampleProcess(fLoc, {
            'normalize': normalize,
            'trim': trim,
            'reverse': reverse,
            'transpose': transpose,
            'pitchShift': pitchShift,
            'pan': pan,
            'volume': volume,
            'filter1On': filter1On,
            'filter1Type': filter1Type,
            'filter1Freq': filter1Freq,
            'filter1Order': filter1Order,
            'filter2On': filter2On,
            'filter2Type': filter2Type,
            'filter2Freq': filter2Freq,
            'filter2Order': filter2Order,
            'startOffset': sampleStart,
            'endOffset': sampleEnd,
            'frames': frames,
            'fadeIn': fadeIn,
            'fadeOut': fadeOut,
            
        }).audio()

        if processed:
            try:
                # Create a buffer to hold the image data
                buffer = BytesIO()
                # Save the image to the buffer
                processed.export(buffer, format='mp3')
                buffer.seek(0)

                # Create a HttpResponse with the PNG data
                response = HttpResponse(buffer, content_type='audio/mpeg')
                return response

            except IOError:
                # Handle the case where the image file does not exist or cannot be opened
                print("Error opening waveform image for sample id:", pk)
                return Response(None, status=status.HTTP_400_BAD_REQUEST)

        # return Response(serializer.data, status=status.HTTP_200_OK)

class SampleProcessView(APIView):
    permission_classes = (AllowAny,)
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer

    def get(self, request, pk=None):
        # For each sample in the DB...
        samples = Sample.objects.all()

        for sample in samples:
            serializer = SampleSerializer(sample)
            fLoc = pjoin("./audio", sample.filename)
            imgData = saveSampleImage(serializer.data)
            print(imgData)
            sample.waveform = imgData['image']

            sample.frames = SampleData(fLoc).length()
            sample.save()
        
        serializer = SampleSerializer(samples, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class TrackSampleView(APIView):
    permission_classes = (AllowAny,)
    queryset = Track.objects.all()
    serializer_class = TrackSerializer

    def get(self, request, pk=None):
        sampleId = request.GET.get('sampleId', None)
        sample = Sample.objects.get(pk=sampleId)
        serializer = SampleSerializer(sample)

        if not sample:
            return Response(None, status=status.HTTP_400_BAD_REQUEST)

        reverse:bool = (request.GET.get('rv', False) in ['true', 'True', True])
        trim:bool = (request.GET.get('tr', False) in ['true', 'True', True])
        normalize:bool = (request.GET.get('nm', False) in ['true', 'True', True])
        transpose:int = int(request.GET.get('ts', 0))
        pitchShift:int = int(request.GET.get('ps', 0))
        pan:int = int(request.GET.get('pn', 0))
        volume:float = float(request.GET.get('vl', 0))

        filter1On:bool = (request.GET.get('f1', False) in ['true', 'True', True])
        filter1Type:str = request.GET.get('ft1', 'lowpass')
        fq1:float = float(request.GET.get('fq1', 0))
        filter1Freq:float = float(fq1)
        filter1Order:float = float(request.GET.get('or1', 0))

        filter2On:bool = (request.GET.get('f2', False) in ['true', 'True', True])
        filter2Type:str = request.GET.get('ft2', 'lowpass')
        fq2:float = float(request.GET.get('fq2', 0))
        filter2Freq:float = float(fq2)
        filter2Order:float = float(request.GET.get('or2', 0))

        sampleStart = request.GET.get('sst', 0)
        sampleEnd = request.GET.get('sen', 0)

        frames:int = sample.frames

        fadeIn = request.GET.get('fi', 0)
        fadeOut = request.GET.get('fo', 0)

        print("frames", frames)
        print("sampl", sample)

        fLoc = pjoin("./audio", sample.filename)

        sampleOptions = {
            'normalize': normalize,
            'trim': trim,
            'reverse': reverse,
            'transpose': transpose,
            'pitchShift': pitchShift,
            'pan': pan,
            'volume': volume,
            'filter1On': filter1On,
            'filter1Type': filter1Type,
            'filter1Freq': filter1Freq,
            'filter1Order': filter1Order,
            'filter2On': filter2On,
            'filter2Type': filter2Type,
            'filter2Freq': filter2Freq,
            'filter2Order': filter2Order,
            'startOffset': sampleStart,
            'endOffset': sampleEnd,
            'frames': frames,
            'fadeIn': fadeIn,
            'fadeOut': fadeOut,
        }


        try:
            info = SampleProcess(fLoc, sampleOptions).info()
            print("info", info)
            response = Response(info, status=status.HTTP_200_OK)

            return response

        except IOError:
            return Response(None, status=status.HTTP_400_BAD_REQUEST)
    