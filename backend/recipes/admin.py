from django.contrib import admin
from django.db.models import Count
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe


from .models import (
    Cart,
    Favorite,
    Ingredient,
    Recipe,
    AmountIngredient,
    User
)


@admin.register(User)
class UserAdminConfig(UserAdmin):
    list_display = (
        "pk",
        "username",
        "full_name",
        "email",
        "avatar_tag",
        "recipes_count",
        "subscriptions_count",
        "subscribers_count",
    )

    @admin.display(description="ФИО")
    def full_name(self, user):
        return f"{user.first_name} {user.last_name}"

    @admin.display(description="Аватар")
    @mark_safe
    def avatar_tag(self, user):
        if user.avatar:
            return f'<img src="{user.avatar.url}" width="50" \
            "height="50" style="object-fit: cover; border-radius: 4px;" />'
        return ""

    @admin.display(description="Рецепты")
    def recipes_count(self, user):
        return user.recipes.count()

    @admin.display(description="Подписки")
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description="Подписчики")
    def subscribers_count(self, user):
        return user.authors.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit', 'recipes_count')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)

    @admin.display(description="Число рецептов", ordering='recipes_count')
    def recipes_count(self, ingredient):
        return ingredient.recipes_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipes_count=Count('ingredient_amounts', distinct=True)
        )


class AmountIngredientInline(admin.TabularInline):
    model = AmountIngredient
    extra = 1
    min_num = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'cooking_time',
        'author',
        'favorites_count',
        'ingredients_list',
        'image_preview',
    )
    list_select_related = ('author',)
    search_fields = ('name', 'author__username')
    inlines = (AmountIngredientInline,)

    @admin.display(description="В избранном", ordering='favorites_count')
    def favorites_count(self, recipe):
        return recipe.favorites_count

    @admin.display(description="Ингредиенты")
    @mark_safe
    def ingredients_list(self, recipe):
        amounts = recipe.ingredient_amounts.select_related('ingredient').all()
        items = '<br>'.join(
            f'{ai.ingredient.name} — '
            f'{ai.amount} {ai.ingredient.measurement_unit}'
            for ai in amounts
        )
        return items

    @admin.display(description="Изображение")
    @mark_safe
    def image_preview(self, recipe):
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" '
                'style="max-height:80px; border-radius:4px;">'
            )
        return ''

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related(
            'ingredient_amounts__ingredient',
        )
        return queryset.annotate(
            favorites_count=Count('favorites', distinct=True)
        )


@admin.register(Favorite, Cart)
class FavoriteAndCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
