# models.py
from django.db import models
from django.contrib.auth.models import User

class Song(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bpm = models.IntegerField(default=120)
    swing = models.FloatField(default=0)
    patternSequence = models.JSONField(default=list)
    author = models.CharField(max_length=100, default='Anonymous')
    lastEdited = models.DateTimeField(auto_now=True)

class Sample(models.Model):
    filename = models.CharField(max_length=100)
    display = models.CharField(max_length=100, null=True)
    waveform = models.ImageField(upload_to='waveforms', null=True)
    frames = models.BigIntegerField(default=0)

class Track(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='tracks')
    name = models.CharField(max_length=100)
    pan = models.FloatField(default=0)
    volume = models.FloatField(default=-6)
    sample = models.ForeignKey(Sample, on_delete=models.SET_NULL, null=True)
    disabled = models.BooleanField(default=False)
    transpose = models.IntegerField(default=0)
    position = models.IntegerField(default=1)
    rootPitch = models.CharField(max_length=5, default='C3')
    pitchShift = models.IntegerField(default=0)
    reverse = models.BooleanField(default=False)
    normalize = models.BooleanField(default=False)
    trim = models.BooleanField(default=False)
    fadeIn = models.PositiveSmallIntegerField(default=0)
    fadeOut = models.PositiveSmallIntegerField(default=0)
    startOffset = models.PositiveIntegerField(default=0)
    endOffset = models.PositiveIntegerField(default=0)
    playMode = models.CharField(max_length=8, default='oneshot')

class Patch(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pan = models.FloatField(default=0)
    volume = models.FloatField(default=-6)
    sample = models.ForeignKey(Sample, on_delete=models.SET_NULL, null=True)
    transpose = models.IntegerField(default=0)
    position = models.IntegerField(default=1)
    rootPitch = models.CharField(max_length=5, default='C3')
    pitchShift = models.IntegerField(default=0)
    reverse = models.BooleanField(default=False)
    normalize = models.BooleanField(default=False)
    trim = models.BooleanField(default=False)
    fadeIn = models.PositiveSmallIntegerField(default=0)
    fadeOut = models.PositiveSmallIntegerField(default=0)
    startOffset = models.PositiveIntegerField(default=0)
    endOffset = models.PositiveIntegerField(default=0)
    playMode = models.CharField(max_length=8, default='oneshot')

class Pattern(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='patterns')
    name = models.CharField(max_length=100)
    bars = models.IntegerField(default=2)
    position = models.IntegerField(default=1)
    pianoIndex = models.JSONField(default=list)

class Step(models.Model):
    pattern = models.ForeignKey(Pattern, related_name='steps', on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    loc = models.CharField(max_length=12, default='1.1.1')
    pitch = models.CharField(max_length=5, default='C3')
    reverse = models.BooleanField(default=False)
    velocity = models.IntegerField(default=100)
    pan = models.FloatField(default=0)
    on = models.BooleanField(default=True)
    duration = models.IntegerField(default=1)
    index = models.IntegerField(default=0)
    retrigger = models.PositiveSmallIntegerField(default=0)

class Filter(models.Model):
    position = models.IntegerField(default=1)
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='filters', null=True)
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='filters', null=True)
    patch = models.ForeignKey(Patch, on_delete=models.CASCADE, related_name='filters', null=True)
    on = models.BooleanField(default=False)
    filter_type = models.CharField(max_length=8, default='lp')
    frequency = models.FloatField(default=2500)
    order = models.PositiveSmallIntegerField(default=1)
