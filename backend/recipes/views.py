from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Recipe, Ingredient, Favorite, Cart, AmountIngredient
from recipes.serializers import (
    RecipeSerializer,
    ShortRecipeSerializer,
    IngredientSerializer,
)
# Предполагается, что фильтр уже реализован
from recipes.filters import RecipeFilter
from recipes.utils import generate_shopping_cart_txt  # или другая функция генерации


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    # Должен поддерживать is_favorited, is_in_shopping_cart, author
    filterset_class = RecipeFilter

    def get_queryset(self):
        # Дополнительная оптимизация (если нужно)
        return super().get_queryset().select_related('author').prefetch_related(
            'tags', 'ingredients'
        )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            raise ValidationError('Рецепт уже в избранном.')
        Favorite.objects.create(user=request.user, recipe=recipe)
        serializer = ShortRecipeSerializer(
            recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = Favorite.objects.filter(
            user=request.user, recipe=recipe).delete()
        if not deleted:
            raise ValidationError('Рецепт не был в избранном.')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if Cart.objects.filter(user=request.user, recipe=recipe).exists():
            raise ValidationError('Рецепт уже в списке покупок.')
        Cart.objects.create(user=request.user, recipe=recipe)
        serializer = ShortRecipeSerializer(
            recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = Cart.objects.filter(
            user=request.user, recipe=recipe).delete()
        if not deleted:
            raise ValidationError('Рецепт не был в списке покупок.')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        cart_recipes = Cart.objects.filter(
            user=user).values_list('recipe_id', flat=True)
        if not cart_recipes:
            return Response(
                {'detail': 'Список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients = (
            AmountIngredient.objects
            .filter(recipe_id__in=cart_recipes)
            .values(
                'ingredient__name',
                'ingredient__measurement_unit'
            )
            .annotate(total_amount=F('amount'))
            .order_by('ingredient__name')
        )

        content = generate_shopping_cart_txt(ingredients)
        response = HttpResponse(
            content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            f'/s/{recipe.id}')  # или через ShortLink модель
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name.lower().strip())
        return queryset
