#_views.py
from django.shortcuts import render

from .views.user import *
from .views.sample import *
from .views.song import *
from .views.pattern import *

def index(request):
  return render(request, 'renderer/index.html')
