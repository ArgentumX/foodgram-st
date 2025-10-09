from django.db import models


class TimeBasedModel(models.Model):
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
        help_text="Создан",
    )
    updated_at = models.DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True,
        help_text="Обновлён",
    )

    class Meta:
        abstract = True
