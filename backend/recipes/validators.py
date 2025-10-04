# core/validators.py
from django.core.exceptions import ValidationError
from django.db import models


def validate_tags(tag_ids, tag_model) -> list:
    """
    Валидация списка ID тегов.
    
    Args:
        tag_ids: list[int] — список ID тегов из запроса.
        tag_model: модель Tag.
    
    Returns:
        list[Tag]: список валидных объектов Tag.
    
    Raises:
        ValidationError: если данные некорректны.
    """
    if not isinstance(tag_ids, list):
        raise ValidationError("Теги должны быть переданы в виде списка.")

    if not tag_ids:
        raise ValidationError("Нужно указать хотя бы один тег.")

    if len(tag_ids) != len(set(tag_ids)):
        raise ValidationError("Теги не должны дублироваться.")

    tags = tag_model.objects.filter(id__in=tag_ids)
    if len(tags) != len(tag_ids):
        raise ValidationError("Указан несуществующий тег.")

    return list(tags)



# core/validators.py (продолжение)

def validate_ingredients(ingredients_data, ingredient_model) -> dict:
    """
    Валидация списка ингредиентов.
    
    Args:
        ingredients_data: list[dict] — [{'id': 1, 'amount': 100}, ...]
        ingredient_model: модель Ingredient.
    
    Returns:
        dict[int, int]: {ingredient_id: amount}
    
    Raises:
        ValidationError: если данные некорректны.
    """
    if not isinstance(ingredients_data, list):
        raise ValidationError("Ингредиенты должны быть переданы в виде списка.")

    if not ingredients_data:
        raise ValidationError("Нужно указать хотя бы один ингредиент.")

    ingredient_ids = []
    amounts = {}

    for item in ingredients_data:
        if not isinstance(item, dict):
            raise ValidationError("Каждый ингредиент должен быть объектом.")

        try:
            ing_id = item["id"]
            amount = item["amount"]
        except KeyError as e:
            raise ValidationError(f"В ингредиенте отсутствует поле: {e}")

        if not isinstance(ing_id, int) or not isinstance(amount, (int, float)):
            raise ValidationError("ID и количество должны быть числами.")

        if amount <= 0:
            raise ValidationError("Количество ингредиента должно быть больше 0.")

        ingredient_ids.append(ing_id)
        amounts[ing_id] = amount

    # Проверка дубликатов
    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise ValidationError("Ингредиенты не должны дублироваться.")

    # Проверка существования
    db_ingredients = ingredient_model.objects.filter(id__in=ingredient_ids)
    if len(db_ingredients) != len(ingredient_ids):
        raise ValidationError("Указан несуществующий ингредиент.")

    return amounts  # {id: amount}