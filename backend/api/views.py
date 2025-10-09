from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
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
from recipes.models import Recipe, Ingredient, Favorite, Cart, AmountIngredient
from .serializers import (
    RecipeSerializer,
    ShortRecipeSerializer,
    IngredientSerializer,
)
from .filters import IngredientFilter, RecipeFilter
from .utils import generate_shopping_cart
from djoser.views import UserViewSet
from .serializers import SubscriptionSerializer, UserSerializer
from users.models import Subscription, User


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related('author').prefetch_related('ingredients')

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

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
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

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
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
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        content = generate_shopping_cart(ingredients)
        response = HttpResponse(
            content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment;' \
            ' filename="shopping_cart.txt"'
        return response

    @action(
        detail=True,
        methods=['get'],
        url_path="get-link"
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            f'/s/{recipe.id}')
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.image:
            recipe.image.delete(save=False)
        self.perform_destroy(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = IngredientFilter
    pagination_class = None
    search_fields = ("^name",)


class CustomUserViewSet(UserViewSet):

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get']
    )
    def subscriptions(self, request):
        authors = User.objects.filter(subscribers__subscriber=request.user)
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete']
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, pk=id)
        if request.user == author:
            return Response({'error': 'Self-subscription is not allowed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # POST
        if request.method == 'POST':
            subscription, created = Subscription.objects.get_or_create(
                subscriber=request.user, author=author
            )
            if not created:
                return Response({'error': 'Already subscribed.'},
                                status=status.HTTP_400_BAD_REQUEST)

            serializer = SubscriptionSerializer(
                author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE
        subscription = Subscription.objects.filter(
            subscriber=request.user, author=author
        ).first()
        if not subscription:
            return Response({'error': 'Not subscribed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        subscription.delete()
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
                return Response(
                    {'avatar': ['Обязательное поле.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = UserSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            avatar_url = None
            if user.avatar:
                avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

        # DELETE
        if not user.avatar:
            return Response(
                {'detail': 'Avatar not set.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.avatar.delete(save=False)
        user.avatar = None
        user.save(update_fields=['avatar'])
        return Response(status=status.HTTP_204_NO_CONTENT)
