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

    def filter_is_favorited(self, queryset, name, value):
        value = bool(value)
        if self.request.user.is_authenticated:
            if value is True:
                return queryset.filter(in_favorites__user=self.request.user)
            elif value is False:
                return queryset.exclude(in_favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        value = bool(value)
        if self.request.user.is_authenticated:
            if value is True:
                return queryset.filter(in_carts__user=self.request.user)
            elif value is False:
                return queryset.exclude(in_carts__user=self.request.user)
        return queryset


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)
