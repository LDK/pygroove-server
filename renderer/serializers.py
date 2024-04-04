# serializers.py
from rest_framework import serializers
from .models import Patch, Pattern, Step, Sample, Filter, Track, Song
from django.contrib.auth.models import User

class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = ['loc', 'track', 'filter', 'pitch', 'reverse', 'velocity', 'pan', 'on', 'duration', 'index']

class FilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filter
        fields = ['on', 'filter_type', 'frequency', 'q', 'position']


class TrackSerializer(serializers.ModelSerializer):
    filters = FilterSerializer(many=True, read_only=True)

    class Meta:
        model = Track
        fields = ['name', 'pan', 'volume', 'sample', 'disabled', 'transpose', 'position', 'filters', 'startOffset', 'endOffset', 'playMode', 'fadeIn', 'fadeOut', 'rootPitch', 'pitchShift', 'reverse', 'normalize', 'trim']

class PatchSerializer(serializers.ModelSerializer):
    filters = FilterSerializer(many=True, read_only=True)

    class Meta:
        model = Patch
        fields = ['name', 'pan', 'volume', 'sample', 'disabled', 'filters', 'pianoIndex', 'startOffset', 'endOffset', 'playMode', 'fadeIn', 'fadeOut', 'rootPitch', 'pitchShift', 'reverse', 'normalize', 'trim']

class PatternSerializer(serializers.ModelSerializer):
    steps = StepSerializer(many=True, read_only=True)

    class Meta:
        model = Pattern
        fields = ['name', 'bars', 'position', 'steps', 'pianoIndex']

class SampleSerializer(serializers.ModelSerializer):
    # For waveform image, return the base64 encoded image
    class Meta:
        model = Sample
        fields = ['id', 'filename', 'display', 'waveform', 'frames']

class SongSerializer(serializers.ModelSerializer):
    tracks = TrackSerializer(many=True, read_only=True)
    patterns = PatternSerializer(many=True, read_only=True)

    class Meta:
        model = Song
        fields = ['id', 'title', 'author', 'bpm', 'swing', 'patternSequence', 'tracks', 'patterns']

class UserSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ('username', 'email', 'password')
    extra_kwargs = {'password': {'write_only': True}}

  def create(self, validated_data):
    return User.objects.create_user(**validated_data)
