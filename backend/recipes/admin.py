from django.contrib import admin
from django.db.models import Count

from .models import (
    Cart,
    Favorite,
    Ingredient,
    Recipe,
    AmountIngredient,
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


class AmountIngredientInline(admin.TabularInline):
    model = AmountIngredient
    extra = 1
    min_num = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count', 'created_at')
    list_select_related = ('author',)
    search_fields = ('name', 'author__username')
    list_filter = ('created_at',)
    inlines = (AmountIngredientInline,)
    ordering = ('-created_at',)

    def favorites_count(self, obj):
        return obj.in_favorites.count()

    favorites_count.short_description = 'Добавлений в избранное'
    favorites_count.admin_order_field = 'favorites_count'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            favorites_count=Count('in_favorites')
        )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'created_at')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'created_at')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
