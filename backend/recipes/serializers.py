# recipes/serializers.py
from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from foodgram.serializers import Base64ImageField
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from recipes.models import Ingredient, Recipe, Tag, AmountIngredient
from .validators import validate_tags, validate_ingredients
from django.db.models import F


class ShortRecipeSerializer(ModelSerializer):
    """Краткое представление рецепта."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields


class TagSerializer(ModelSerializer):
    """Сериализатор тегов (только чтение)."""

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")
        read_only_fields = fields


class IngredientSerializer(ModelSerializer):
    """Сериализатор ингредиентов (только чтение)."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = fields


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

    tags = TagSerializer(many=True, read_only=True)
    author = SerializerMethodField()
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = (
            "author",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_author(self, obj):
        # Предполагается, что UserSerializer находится в users/serializers.py
        from users.serializers import UserSerializer
        return UserSerializer(obj.author, context=self.context).data

    def get_is_favorited(self, recipe):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and user.favorites.filter(recipe=recipe).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and user.carts.filter(recipe=recipe).exists()
        )

    def validate(self, attrs):
        tags_data = self.initial_data.get("tags")
        ingredients_data = self.initial_data.get("ingredients")

        attrs["tags"] = validate_tags(tags_data, Tag)
        attrs["ingredients"] = validate_ingredients(
            ingredients_data, Ingredient)

        name = attrs.get('name')
        author = self.context['request'].user
        if name and Recipe.objects.filter(name=name, author=author).exists():
            raise ValidationError("У вас уже есть рецепт с таким названием.")

        return attrs

    @atomic
    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
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
        tags = validated_data.pop("tags", None)
        ingredients = validated_data.pop("ingredients", None)

        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if tags is not None:
            instance.tags.set(tags)
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
