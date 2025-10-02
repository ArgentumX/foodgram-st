from django.db import models
from django.contrib.auth.models import AbstractUser

from foodgram.models import TimeBasedModel


class User(AbstractUser, TimeBasedModel):
    email = models.EmailField(
        verbose_name='Email',
        unique=True,
        max_length=254,
    )
    first_name = models.CharField(max_length=48, blank=False)
    last_name = models.CharField(max_length=48, blank=False)
    avatar = models.ImageField(
        verbose_name='Avatar',
        upload_to='users/media/',
        null=True,
        blank=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'first_name',
        'last_name',
        'username'
    ]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(TimeBasedModel):
    author = models.ForeignKey(
        verbose_name="Автор рецепта",
        related_name="subscribers",
        to=User,
        on_delete=models.CASCADE,
    )
    subscriber = models.ForeignKey(
        verbose_name="Подписчики",
        related_name="subscriptions",
        to=User,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.subscriber} → {self.author}"

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'author'],
                name='Already subscibed'
            ),
            models.CheckConstraint(
                check=~models.Q(subscriber=models.F('author')),
                name='No self subscribtions'
            ),
        ]
