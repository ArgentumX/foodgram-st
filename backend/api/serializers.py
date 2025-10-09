# recipes/serializers.py
from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from foodgram.serializers import Base64ImageField
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    ReadOnlyField,
    UniqueTogetherValidator
)
from recipes.models import Cart, Favorite, Ingredient, Recipe, AmountIngredient
from .validators import validate_ingredients
from djoser import serializers as djoser_serializers

from users.models import User


class ShortRecipeSerializer(ModelSerializer):
    """Краткое представление рецепта."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields


class IngredientSerializer(ModelSerializer):
    """Сериализатор ингредиентов (только чтение)."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = fields


class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        ]
        read_only_fields = ['id']


class UserSerializer(djoser_serializers.UserSerializer):
    is_subscribed = SerializerMethodField()
    avatar = Base64ImageField(required=False)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if (
            not request 
            or not request.user.is_authenticated 
            or request.user == obj
        ):
            return False
        return obj.subscribers.filter(subscriber=request.user).exists()

    class Meta(djoser_serializers.UserSerializer.Meta):
        model = User
        fields = [
            'id',
            'username',
            'email',
            'avatar',
            'first_name',
            'last_name',
            'is_subscribed'
        ]


class SubscriptionSerializer(UserSerializer):
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta(UserSerializer.Meta):
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        return True

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request:
            recipes = obj.recipes.all()
        else:
            limit = request.query_params.get('recipes_limit')
            recipes = obj.recipes.all()
            if limit and limit.isdigit() and int(limit) >= 0:
                recipes = recipes[:int(limit)]

        serializer = ShortRecipeSerializer(
            recipes,
            many=True,
            context={'request': request}
        )
        return serializer.data


class AmountIngredientSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = AmountIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = [
            UniqueTogetherValidator(
                queryset=AmountIngredient.objects.all(),
                fields=['ingredient', 'recipe']
            )
        ]


class RecipeSerializer(ModelSerializer):
    """Полный сериализатор рецепта."""
    author = UserSerializer(read_only=True)
    ingredients = AmountIngredientSerializer(
        source='ingredient_amounts',
        many=True,
        read_only=True,
    )
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "text",
            "image",
            "cooking_time",
        )
        read_only_fields = (
            "id",
            "author",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Cart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def validate(self, attrs):

        text = self.initial_data.get("text", None)
        if not text:
            raise ValidationError("Вы не указали текст")

        ingredients_data = self.initial_data.get("ingredients")

        attrs["ingredients"] = validate_ingredients(
            ingredients_data, Ingredient)

        name = attrs.get('name')
        author = self.context['request'].user
        if name and Recipe.objects.filter(name=name, author=author).exists():
            raise ValidationError("У вас уже есть рецепт с таким названием.")

        return attrs

    @atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        recipe_ingredients = [
            AmountIngredient(
                recipe=recipe,
                ingredient_id=ing_id,
                amount=amount
            )
            for ing_id, amount in ingredients.items()
        ]

        AmountIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    @atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients", None)

        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if ingredients is not None:
            instance.ingredients.clear()
            recipe_ingredients = [
                AmountIngredient(
                    recipe=instance,
                    ingredient_id=ing_id,
                    amount=amount
                )
                for ing_id, amount in ingredients.items()
            ]

            AmountIngredient.objects.bulk_create(recipe_ingredients)

        instance.save()
        return instance
