
from rest_framework.permissions import AllowAny

from renderer.serializers import UserSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from renderer.models import Song

class UserView(APIView):
    def get(self, request):
        return Response({
          'username': request.user.username,
          'id': request.user.id,
          'email': request.user.email,
        })

class UserSongsView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
          return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        songs = Song.objects.filter(user=request.user)

        songPatterns = {}
        songTracks = {}

        for song in songs:
          patterns = song.patterns.all()
          tracks = song.tracks.all()

          patternList = []

          for pattern in patterns:
            # First we gather all the steps for each pattern
            stepList = []

            for step in pattern.steps.all():
              filterList = []
              for filter in step.filters.all():
                filterList.append({
                  'id': filter.id,
                  'filter_type': filter.filter_type,
                  'frequency': filter.frequency,
                  'q': filter.q,
                  'on': filter.on,
                  'position': filter.position,
                })

              loc = step.loc.split('.')

              trackFilters = []
              for filter in step.track.filters.all():
                trackFilters.append({
                  'id': filter.id,
                  'filter_type': filter.filter_type,
                  'frequency': filter.frequency,
                  'q': filter.q,
                  'on': filter.on,
                  'position': filter.position,
                })

              track = {
                'id': step.track.id,
                'name': step.track.name,
                'pan': step.track.pan,
                'volume': step.track.volume,
                'disabled': step.track.disabled,
                'transpose': step.track.transpose,
                'position': step.track.position,
                'normalize': step.track.normalize,
                'pitchShift': step.track.pitchShift,
                'playMode': step.track.playMode,
                'reverse': step.track.reverse,
                'rootPitch': step.track.rootPitch,
                'endOffset': step.track.endOffset,
                'startOffset': step.track.startOffset,
                'fadeIn': step.track.fadeIn,
                'fadeOut': step.track.fadeOut,
                'trim': step.track.trim,
                'sample': {
                  'id': step.track.sample.id,
                  'filename': step.track.sample.filename,
                  'display': step.track.sample.display,
                  'waveform': step.track.sample.waveform.url if step.track.sample.waveform else None,
                },
                'filters': trackFilters
              }

              stepList.append({
                'id': step.id,
                'loc': {
                  'bar': loc[0],
                  'beat': loc[1],
                  'tick': loc[2],
                },
                'pitch': step.pitch,
                'reverse': step.reverse,
                'velocity': step.velocity,
                'pan': step.pan,
                'index': step.index,
                'on': step.on if step.on else False,
                'duration': step.duration if step.duration else 1,
                'filters': filterList,
                'track': track,
              })

            patternList.append({
              'id': pattern.id,
              'name': pattern.name,
              'position': pattern.position,
              'bars': pattern.bars,
              'steps': stepList,
            })
          
          songPatterns[song.id] = patternList

          trackList = []

          for track in tracks:
            # First find the associated Sample
            sample = {
              'id': track.sample.id,
              'filename': track.sample.filename,
              'display': track.sample.display,
              'waveform': track.sample.waveform.url if track.sample.waveform else None,
            }

            # Then gather all the filters for each track
            filterList = []
            for filter in track.filters.all():
              filterList.append({
                'id': filter.id,
                'filter_type': filter.filter_type,
                'frequency': filter.frequency,
                'q': filter.q,
                'on': filter.on,
                'position': filter.position,
              })

            trackList.append({
              'id': track.id,
              'name': track.name,
              'pan': track.pan,
              'volume': track.volume,
              'disabled': track.disabled,
              'transpose': track.transpose,
              'position': track.position,
              'normalize': track.normalize,
              'pitchShift': track.pitchShift,
              'playMode': track.playMode,
              'reverse': track.reverse,
              'rootPitch': track.rootPitch,
              'endOffset': track.endOffset,
              'startOffset': track.startOffset,
              'fadeIn': track.fadeIn,
              'fadeOut': track.fadeOut,
              'trim': track.trim,
              'sample': sample,
              'filters': filterList,
            })

          songTracks[song.id] = trackList

        return Response([{
          'id': song.id,
          'title': song.title,
          'author': song.author,
          'bpm': song.bpm,
          'swing': song.swing,
          'lastEdited': song.lastEdited,
          'patternSequence': song.patternSequence,
          'patterns': songPatterns[song.id],
          'tracks': songTracks[song.id],
        } for song in songs])

class RefreshTokenView(TokenRefreshView):
    permission_classes = (AllowAny,)

class CreateUserView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            User.objects.create_user(**serializer.validated_data)

            user = authenticate(
              username=serializer.validated_data['username'],
              password=serializer.validated_data['password']
            )

            refresh = RefreshToken.for_user(user)

            return Response({
              'username': user.username,
              'id': user.id,
              'email': user.email,
              'token': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
              }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
  permission_classes = (AllowAny,)

  def post(self, request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)

    if user is not None:
      refresh = RefreshToken.for_user(user)
      return Response({
         'username': user.username,
         'id': user.id,
         'email': user.email,
         'token': {
          'refresh': str(refresh),
          'access': str(refresh.access_token),
         }
      })
    
    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

