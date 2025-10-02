from django.urls import include, path
from .views import CustomUserViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register('users', CustomUserViewSet, basename='users')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
