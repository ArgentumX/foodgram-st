from django.db import models
from django.db.models.functions import Length
from django.contrib.auth.models import AbstractUser
from rest_framework.exceptions import ValidationError
from django.db.models import (
    CASCADE,
    F,
    CharField,
    CheckConstraint,
    EmailField,
    ForeignKey,
    ImageField,
    ManyToManyField,
    PositiveSmallIntegerField,
    Q,
    TextField,
    UniqueConstraint,
)
from django.conf import settings
from django.core.validators import (
    MinValueValidator,
    RegexValidator
)

MAX_LEN_RECIPES_CHARFIELD = 200
MAX_LEN_RECIPES_TEXTFIELD = 2000

CharField.register_lookup(Length)


class User(AbstractUser):
    username = CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9._-]+$',
                message='Имя пользователя может содержать только'
                ' латинские буквы, цифры, дефис и подчёркивание.',
                code='invalid_username'
            )
        ],
        verbose_name='Имя пользователя'
    )

    email = EmailField(
        verbose_name='Email',
        unique=True,
        max_length=254,
    )
    first_name = CharField(max_length=30, blank=False, verbose_name='Имя')
    last_name = CharField(max_length=30, blank=False, verbose_name='Фамилия')
    avatar = ImageField(
        verbose_name='Аватар',
        upload_to=settings.USER_AVATARS_MEDIA_PATH,
        null=True,
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ("username",)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    author = ForeignKey(
        verbose_name="Авторы",
        related_name="authors",
        to=User,
        on_delete=CASCADE,
    )
    subscriber = ForeignKey(
        verbose_name="Подписчики",
        related_name="subscriptions",
        to=User,
        on_delete=CASCADE,
    )

    def __str__(self):
        return f"{self.subscriber} → {self.author}"

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ("author__username",)
        constraints = [
            UniqueConstraint(
                fields=['subscriber', 'author'],
                name='Already subscibed'
            ),
            CheckConstraint(
                check=~Q(subscriber=F('author')),
                name='No self subscribtions'
            ),
        ]


HEX_COLOR_VALIDATOR = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Цвет должен быть указан в формате HEX: #RRGGBB"
)


# Проверка на уникальность пары полей: Имеется,
# Добавление uniquе=True сделает проверку уникальности пары полей бессмысленной
class Ingredient(models.Model):
    name = CharField(
        verbose_name="Продукт",
        max_length=MAX_LEN_RECIPES_CHARFIELD,
    )
    measurement_unit = CharField(
        verbose_name="Единица измерения",
        max_length=64
    )

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ("name",)
        constraints = (
            UniqueConstraint(fields=("name", "measurement_unit"),
                             name="unique_pair"),
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    name = CharField(
        verbose_name="Название блюда",
        max_length=MAX_LEN_RECIPES_CHARFIELD,
    )
    author = ForeignKey(
        verbose_name="Автор рецепта",
        related_name="recipes",
        to=User,
        on_delete=CASCADE,
    )
    ingredients = ManyToManyField(
        verbose_name="Ингредиенты",
        related_name="recipes",
        to=Ingredient,
        through="AmountIngredient",
        blank=True,
    )
    image = ImageField(
        verbose_name="Изображение блюда",
        upload_to=settings.RECIPE_IMAGES_MEDIA_PATH,
        blank=True,
    )
    text = TextField(
        verbose_name="Описание блюда",
        max_length=MAX_LEN_RECIPES_TEXTFIELD,
        blank=True,
    )
    cooking_time = PositiveSmallIntegerField(
        verbose_name="Время приготовления (в минутах)",
        validators=[
            MinValueValidator(
                settings.MIN_COOKING_TIME,
                message=(
                    f"Время приготовления не может быть меньше "
                    f"{settings.MIN_COOKING_TIME} минуты."
                )
            )
        ],
    )

    def clean(self):
        super().clean()
        if not self.name or not self.name.strip():
            raise ValidationError(
                {"name": "Название блюда не может быть пустым."})

        if len(self.name.strip()) < 2:
            raise ValidationError(
                {"name": "Название блюда должно содержать хотя бы 2 символа."})

        if self.text and not self.text.strip():
            raise ValidationError(
                {"text": "Описание не может состоять только из пробелов."})

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        constraints = (
            UniqueConstraint(fields=("name", "author"),
                             name="unique_recipe_per_author"),
        )

    def __str__(self) -> str:
        return self.name


class AmountIngredient(models.Model):
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
                message=(
                    f"Количество ингредиента должно быть не менее "
                    f"{settings.MIN_AMOUNT_INGREDIENTS}."
                )
            )
        ],
    )

    class Meta:
        verbose_name = "Количество ингредиента"
        verbose_name_plural = "Количество ингредиентов"
        ordering = ("recipe",)
        constraints = (
            UniqueConstraint(
                fields=("recipe", "ingredient"),
                name="unique_ingredient_in_recipe"
            ),
        )

    def __str__(self) -> str:
        return (
            f"{self.ingredient.name} — {self.amount} "
            f"{self.ingredient.measurement_unit}"
        )


class UserRecipeRelation(models.Model):
    recipe = models.ForeignKey(
        verbose_name="Рецепт",
        to=Recipe,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )
    user = models.ForeignKey(
        verbose_name="Пользователь",
        to=User,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=("recipe", "user"),
                name="unique_%(class)s_per_user",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.user} добавил(а) в"
            f"{self._meta.verbose_name}: {self.recipe}"
        )


class Favorite(UserRecipeRelation):
    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"


class Cart(UserRecipeRelation):
    class Meta:
        verbose_name = "Рецепт в списке покупок"
        verbose_name_plural = "Рецепты в списке покупок"
