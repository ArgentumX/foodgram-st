from typing import Optional

from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db.models import (
    CASCADE,
    SET_NULL,
    CharField,
    CheckConstraint,
    DateTimeField,
    ForeignKey,
    ImageField,
    ManyToManyField,
    PositiveSmallIntegerField,
    Q,
    TextField,
    UniqueConstraint,
)
from django.db.models.functions import Length

from foodgram.models import TimeBasedModel

CharField.register_lookup(Length)

User = get_user_model()

HEX_COLOR_VALIDATOR = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Цвет должен быть указан в формате HEX: #RRGGBB (например, #FF5733)."
)


class Tag(TimeBasedModel):
    name = CharField(
        verbose_name="Тег",
        max_length=settings.MAX_LEN_RECIPES_CHARFIELD,
        unique=True,
    )
    color = CharField(
        verbose_name="Цвет (HEX)",
        max_length=7,
        unique=True,
        validators=[HEX_COLOR_VALIDATOR],
    )
    slug = CharField(
        verbose_name="Slug",
        max_length=settings.MAX_LEN_RECIPES_CHARFIELD,
        unique=True,
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ("name",)
        constraints = (
            CheckConstraint(check=Q(name__length__gt=0),
                            name="tag_name_not_empty"),
            CheckConstraint(check=Q(slug__length__gt=0),
                            name="tag_slug_not_empty"),
        )

    def __str__(self) -> str:
        return f"{self.name} (цвет: {self.color})"

    def clean(self) -> None:
        if self.name:
            self.name = self.name.strip().lower()
        if self.slug:
            self.slug = self.slug.strip().lower()
        if self.color:
            color = self.color.strip()
            if not color.startswith("#"):
                color = f"#{color}"
            try:
                HEX_COLOR_VALIDATOR(color)
            except ValidationError:
                raise ValidationError({"color": "Некорректный HEX-код цвета."})
            self.color = color
        super().clean()


class Ingredient(TimeBasedModel):
    name = CharField(
        verbose_name="Ингредиент",
        max_length=settings.MAX_LEN_RECIPES_CHARFIELD,
    )
    measurement_unit = CharField(
        verbose_name="Единица измерения",
        max_length=24,
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)
        constraints = (
            UniqueConstraint(fields=("name", "measurement_unit"),
                             name="unique_ingredient_name_unit"),
            CheckConstraint(check=Q(name__length__gt=0),
                            name="ingredient_name_not_empty"),
            CheckConstraint(check=Q(measurement_unit__length__gt=0),
                            name="ingredient_unit_not_empty"),
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.measurement_unit})"

    def clean(self) -> None:
        if self.name:
            self.name = self.name.strip().lower()
        if self.measurement_unit:
            self.measurement_unit = self.measurement_unit.strip().lower()
        super().clean()


class Recipe(TimeBasedModel):
    name = CharField(
        verbose_name="Название блюда",
        max_length=settings.MAX_LEN_RECIPES_CHARFIELD,
    )
    author = ForeignKey(
        verbose_name="Автор рецепта",
        related_name="recipes",
        to=User,
        on_delete=SET_NULL,
        null=True,
        blank=True,
    )
    tags = ManyToManyField(
        verbose_name="Теги",
        related_name="recipes",
        to="Tag",
        blank=True,
    )
    ingredients = ManyToManyField(
        verbose_name="Ингредиенты",
        related_name="recipes",
        to=Ingredient,
        through="AmountIngredient",
        blank=True,
    )
    pub_date = DateTimeField(
        verbose_name="Дата публикации", auto_now_add=True, editable=False
    )
    image = ImageField(
        verbose_name="Изображение блюда",
        upload_to="recipe_images/",
        blank=True,
    )
    text = TextField(
        verbose_name="Описание блюда",
        max_length=settings.MAX_LEN_RECIPES_TEXTFIELD,
        blank=True,
    )
    cooking_time = PositiveSmallIntegerField(
        verbose_name="Время приготовления (в минутах)",
        validators=[
            MinValueValidator(
                settings.MIN_COOKING_TIME,
                message=f"Время приготовления не может быть меньше {settings.MIN_COOKING_TIME} минуты."
            ),
            MaxValueValidator(
                settings.MAX_COOKING_TIME,
                message=f"Время приготовления не может превышать {settings.MAX_COOKING_TIME} минут."
            ),
        ],
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)
        constraints = (
            UniqueConstraint(fields=("name", "author"),
                             name="unique_recipe_per_author"),
            CheckConstraint(check=Q(name__length__gt=0),
                            name="recipe_name_not_empty"),
        )

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        if self.name:
            self.name = self.name.strip().capitalize()
        super().clean()

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)

        if not self.image:
            return

        image_path = getattr(self.image, "path", None)
        if not image_path:
            return

        with Image.open(image_path) as img:
            img.thumbnail(settings.RECIPE_IMAGE_SIZE)
            img.save(image_path)


class AmountIngredient(TimeBasedModel):
    recipe = ForeignKey(
        verbose_name="Рецепт",
        related_name="ingredient_amounts",
        to=Recipe,
        on_delete=CASCADE,
    )
    ingredient = ForeignKey(
        verbose_name="Ингредиент",
        related_name="recipe_amounts",
        to=Ingredient,
        on_delete=CASCADE,
    )
    amount = PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(
                settings.MIN_AMOUNT_INGREDIENTS,
                message=f"Количество ингредиента должно быть не менее {settings.MIN_AMOUNT_INGREDIENTS}."
            ),
            MaxValueValidator(
                settings.MAX_AMOUNT_INGREDIENTS,
                message=f"Количество ингредиента не может превышать {settings.MAX_AMOUNT_INGREDIENTS}."
            ),
        ],
    )

    class Meta:
        verbose_name = "Количество ингредиента"
        verbose_name_plural = "Количество ингредиентов"
        ordering = ("recipe",)
        constraints = (
            UniqueConstraint(fields=("recipe", "ingredient"),
                             name="unique_ingredient_in_recipe"),
            # CheckConstraint для amount__gte=0 удалён — избыточен для PositiveSmallIntegerField
        )

    def __str__(self) -> str:
        return f"{self.amount} {self.ingredient.measurement_unit} {self.ingredient.name}"


class Favorite(TimeBasedModel):
    recipe = ForeignKey(
        verbose_name="Рецепт",
        related_name="in_favorites",
        to=Recipe,
        on_delete=CASCADE,
    )
    user = ForeignKey(
        verbose_name="Пользователь",
        related_name="favorites",
        to=User,
        on_delete=CASCADE,
    )
    date_added = DateTimeField(
        verbose_name="Дата добавления", auto_now_add=True, editable=False
    )

    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        constraints = (
            UniqueConstraint(fields=("recipe", "user"),
                             name="unique_favorite_per_user"),
        )

    def __str__(self) -> str:
        return f"{self.user} добавил(а) в избранное: {self.recipe}"


class Cart(TimeBasedModel):
    recipe = ForeignKey(
        verbose_name="Рецепт",
        related_name="in_carts",
        to=Recipe,
        on_delete=CASCADE,
    )
    user = ForeignKey(
        verbose_name="Владелец списка",
        related_name="carts",
        to=User,
        on_delete=CASCADE,
    )
    date_added = DateTimeField(
        verbose_name="Дата добавления", auto_now_add=True, editable=False
    )

    class Meta:
        verbose_name = "Рецепт в списке покупок"
        verbose_name_plural = "Рецепты в списке покупок"
        constraints = (
            UniqueConstraint(fields=("recipe", "user"),
                             name="unique_cart_item_per_user"),
        )

    def __str__(self) -> str:
        return f"{self.user} добавил(а) в корзину: {self.recipe}"
