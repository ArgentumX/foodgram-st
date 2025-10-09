from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet, RecipeViewSet, IngredientViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientViewSet,
                basename='ingredients')
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularSwaggerView,
        SpectacularRedocView
    )
    urlpatterns += [
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path(
            'swagger/',
            SpectacularSwaggerView.as_view(url_name='schema'),
            name='swagger-ui'),
        path(
            'redoc/',
            SpectacularRedocView.as_view(url_name='schema'),
            name='redoc'
        )
    ]
