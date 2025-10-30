# recipes/serializers.py
from django.db.transaction import atomic
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    ImageField,
    IntegerField,
    ValidationError,
    PrimaryKeyRelatedField,
    FloatField,
    UniqueTogetherValidator,
    ReadOnlyField,
    CharField,
)
from django.core.validators import MinValueValidator
from recipes.models import Cart, Favorite, Ingredient, Recipe, AmountIngredient
from djoser import serializers as djoser_serializers

from recipes.models import User
import base64
import binascii
import uuid
from django.conf import settings
from django.core.files.base import ContentFile


class Base64ImageField(ImageField):
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    DEFAULT_MAX_SIZE = settings.DEFAULT_CLIENT_MAX_FILESIZE

    def __init__(self, *args, max_size=None, **kwargs):
        self.max_size = (
            max_size
            if max_size is not None
            else self.DEFAULT_MAX_SIZE
        )
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if not isinstance(data, str) or not data.startswith('data:image'):
            return super().to_internal_value(data)

        try:
            header, encoded_data = data.split(';base64,', 1)
        except ValueError:
            raise ValidationError(
                "Неверный формат base64-изображения.")

        try:
            mime_type = header.replace('data:', '')
            ext = mime_type.split('/')[-1].lower()
        except IndexError:
            raise ValidationError(
                "Не удалось определить расширение изображения.")

        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                "Поддерживаются только изображения"
                " в форматах JPG, JPEG, PNG или GIF."
            )

        try:
            decoded = base64.b64decode(encoded_data)
        except (TypeError, binascii.Error, ValueError):
            raise ValidationError(
                "Неверный формат base64-изображения.")

        if len(decoded) > self.max_size:
            max_mb = self.max_size // (1024 * 1024)
            raise ValidationError(
                f"Размер изображения не должен превышать {max_mb} МБ."
            )

        filename = f"{uuid.uuid4().hex[:10]}.{ext}"
        file = ContentFile(decoded, name=filename)
        return super().to_internal_value(file)


class ShortRecipeSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class UserSerializer(djoser_serializers.UserSerializer):
    is_subscribed = SerializerMethodField()
    avatar = Base64ImageField(required=False)

    def get_is_subscribed(self, user):
        request = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and request.user != user
            and user.authors.filter(subscriber=request.user).exists()
        )

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
        read_only_fields = fields


class UserWithAdditionalInfoSerializer(UserSerializer):
    recipes = SerializerMethodField()
    recipes_count = IntegerField(source='recipes.count', read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            "recipes",
            "recipes_count",
        ]
        read_only_fields = fields

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()

        if request:
            limit = request.GET.get('recipes_limit')
            if limit and limit.isdigit() and int(limit) >= 0:
                recipes = recipes[:int(limit)]

        serializer = ShortRecipeSerializer(
            recipes,
            many=True,
            context={'request': request}
        )
        return serializer.data


class AmountIngredientSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = FloatField(
        validators=[MinValueValidator(
            1,
            message="Количество должно быть не меньше 1."
        )]
    )

    class Meta:
        model = AmountIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = [
            UniqueTogetherValidator(
                queryset=AmountIngredient.objects.all(),
                fields=('ingredient', 'recipe')
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
    text = CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True
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
        ingredients_data = self.initial_data.get("ingredients")
        if not ingredients_data:
            raise ValidationError("Нужно указать хотя бы один ингредиент.")

        seen_ids = set()
        validated_ingredients = []

        for item in ingredients_data:
            ing_id = item["id"]
            amount = item["amount"]
            if amount < 1:
                raise ValidationError(
                    "Количество ингредиента должно быть больше 0."
                )

            if ing_id in seen_ids:
                raise ValidationError(
                    f"Ингредиенты не должны дублироваться: {ing_id}"
                )
            seen_ids.add(ing_id)
            validated_ingredients.append(
                {"ingredient_id": ing_id, "amount": amount}
            )

        existing_ids = set(
            Ingredient.objects.filter(id__in=seen_ids).values_list(
                "id", flat=True
            )
        )
        if len(existing_ids) != len(seen_ids):
            missing = seen_ids - existing_ids
            raise ValidationError(
                f"Ингредиенты с ID {missing} не существуют."
            )

        attrs["ingredients"] = validated_ingredients
        return attrs

    @atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        recipe = super().create(validated_data)
        self._set_ingredients(recipe, ingredients_data)
        return recipe

    @atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        recipe = super().update(instance, validated_data)
        if ingredients_data is not None:
            self._set_ingredients(recipe, ingredients_data)
        return recipe

    def _set_ingredients(self, recipe, ingredients_data):
        recipe.ingredients.clear()
        recipe_ingredients = [
            AmountIngredient(
                recipe=recipe,
                ingredient_id=item['ingredient_id'],
                amount=item['amount']
            )
            for item in ingredients_data
        ]
        AmountIngredient.objects.bulk_create(recipe_ingredients)
