import django_filters
from recipes.models import Ingredient, Recipe


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart')
    author = django_filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, recipes, name, value):
        value = bool(value)
        if self.request.user.is_authenticated:
            if value:
                return recipes.filter(favorites__user=self.request.user)
            elif not value:
                return recipes.exclude(favorites__user=self.request.user)
        return recipes

    def filter_is_in_shopping_cart(self, recipes, name, value):
        value = bool(value)
        if self.request.user.is_authenticated:
            if value:
                return recipes.filter(carts__user=self.request.user)
            elif not value:
                return recipes.exclude(carts__user=self.request.user)
        return recipes


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)
