from django.urls import include, path
from rest_framework.routers import DefaultRouter

from recipes import views as recipe_views

router = DefaultRouter()
router.register(r'recipes', recipe_views.RecipeViewSet, basename='recipe')
router.register(r'ingredients', recipe_views.IngredientViewSet,
                basename='ingredient')

urlpatterns = [
    path('', include(router.urls)),
]
