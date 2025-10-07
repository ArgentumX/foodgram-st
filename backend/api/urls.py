from django.urls import include, path
from rest_framework.routers import DefaultRouter

from django.urls import include, path
from .views import CustomUserViewSet, RecipeViewSet, IngredientViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientViewSet,
                basename='ingredient')
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
