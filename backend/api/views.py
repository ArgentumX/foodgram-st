from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated
)
from rest_framework.response import Response

from .permissions import IsOwnerOrReadOnly
from recipes.models import Recipe, Ingredient, Favorite, Cart, \
    AmountIngredient, Subscription
from .serializers import (
    RecipeSerializer,
    ShortRecipeSerializer,
    IngredientSerializer,
    User
)
from .filters import IngredientFilter, RecipeFilter
from .utils import generate_shopping_cart
from djoser.views import UserViewSet as DjoserUserViewSet
from .serializers import UserWithAdditionalInfoSerializer, UserSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects \
        .select_related('author') \
        .prefetch_related('ingredients') \
        .all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        data = self._add_to_relation(
            user=request.user,
            recipe=recipe,
            model=Favorite,
            error_message_exists=f'Рецепт {recipe.name} уже в избранном.',
            request=request  # ← добавьте эту строку
        )
        return Response(data, status=status.HTTP_201_CREATED)
    
    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        self._remove_from_relation(
            user=request.user,
            recipe=recipe,
            model=Favorite,
            error_message_not_found='Рецепт не был в избранном.'
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        data = self._add_to_relation(
            user=request.user,
            recipe=recipe,
            model=Cart,
            error_message_exists='Рецепт уже в списке покупок.',
            request=request  
        )
        return Response(data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        self._remove_from_relation(
            user=request.user,
            recipe=recipe,
            model=Cart,
            error_message_not_found='Рецепт не был в списке покупок.'
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _add_to_relation(user, recipe, model, error_message_exists, request):
        if model.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(error_message_exists)
        model.objects.create(user=user, recipe=recipe)
        return ShortRecipeSerializer(recipe, context={'request': request}).data

    @staticmethod
    def _remove_from_relation(user, recipe, model, error_message_not_found):
        deleted, _ = model.objects.filter(user=user, recipe=recipe).delete()
        if not deleted:
            raise ValidationError(error_message_not_found)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        cart_items = user.carts

        if not cart_items.exists():
            raise ValidationError('Список покупок пуст.')

        ingredients = (
            AmountIngredient.objects
            .filter(recipe__in=cart_items.values_list('recipe', flat=True))
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        recipes = (
            cart_items
            .select_related('recipe__author')
            .values('recipe__name', 'recipe__author__username')
        )

        content = generate_shopping_cart(ingredients, recipes)
        response = FileResponse(
            content.encode('utf-8'),
            content_type='text/plain; charset=utf-8',
            as_attachment=True,
            filename='shopping_cart.txt'
        )
        return response

    @action(detail=True, methods=['get'], url_path="get-link")
    def get_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise Response(status=status.HTTP_404_NOT_FOUND)
        return Response(
            {'short-link':
                request.build_absolute_uri(reverse(
                    'recipe-short-link',
                    kwargs={'pk': pk}))},
            status=status.HTTP_200_OK
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = IngredientFilter
    pagination_class = None
    search_fields = ("^name",)


class UserViewSet(DjoserUserViewSet):

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get']
    )
    def subscriptions(self, request):
        authors = User.objects.filter(authors__subscriber=request.user)
        page = self.paginate_queryset(authors)
        serializer = UserWithAdditionalInfoSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, id):
        if request.method == 'POST':
            author = get_object_or_404(User, pk=id)
            if request.user == author:
                raise ValidationError('Self-subscription is not allowed.')
            _, created = Subscription.objects.get_or_create(
                subscriber=request.user,
                author=author
            )
            if not created:
                raise ValidationError('Already subscribed.')

            serializer = UserWithAdditionalInfoSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE
        get_object_or_404(
            Subscription,
            subscriber=request.user,
            author_id=id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                raise ValidationError({'avatar': ['Обязательное поле.']})

            serializer = UserSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            avatar_url = (
                request.build_absolute_uri(user.avatar.url)
                if user.avatar else None
            )
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

        # DELETE
        if not user.avatar:
            raise ValidationError({'detail': 'Avatar not set.'})

        user.avatar.delete(save=False)
        user.avatar = None
        user.save(update_fields=['avatar'])
        return Response(status=status.HTTP_204_NO_CONTENT)