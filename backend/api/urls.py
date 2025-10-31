from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RecipeViewSet, IngredientViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientViewSet,
                basename='ingredients')
router.register('users', UserViewSet, basename='users')

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
        # Redoc is only for not-Docker dev setup
        path(
            'redoc/',
            SpectacularRedocView.as_view(url_name='schema'),
            name='redoc'
        ),
        path(
            'swagger/',
            SpectacularSwaggerView.as_view(url_name='schema'),
            name='swagger-ui'),
    ]
