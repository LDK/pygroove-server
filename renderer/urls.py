from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import _views as views

router = DefaultRouter()
router.register(r'songs', views.SongViewSet)
router.register(r'samples', views.SampleListSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.CreateUserView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('user/', views.UserView.as_view(), name='user'),
    path('user/songs', views.UserSongsView.as_view(), name='user_songs'),
    path('render/', views.RenderView.as_view(), name='render'),
    path('sample/', views.CreateSampleView.as_view(), name='sample'),
    path('sample/<int:pk>/', views.SampleView.as_view(), name='sample'),
    path('sample/<int:pk>/waveform', views.SampleImageView.as_view(), name='sample_waveform'),
    path('sample/<int:pk>/preview', views.SampleAudioView.as_view(), name='sample_preview'),
    path('pattern/preview/', views.PreviewPatternView.as_view(), name='pattern_preview'),
    path('pattern/piano/', views.PianoPatternView.as_view(), name='pattern_piano'),
    path('track/sample', views.TrackSampleView.as_view(), name='track_sample'),
    path('samples/process', views.SampleProcessView.as_view(), name='sample_process'),
    path('song/', views.CreateSongView.as_view(), name='song'),
    path('song/<int:pk>/', views.SongView.as_view(), name='song'),
    path('song/<int:pk>/rename/', views.RenameSongView.as_view(), name='song_rename'),
    path('token/refresh/', views.RefreshTokenView.as_view(), name='token_refresh'),
]
