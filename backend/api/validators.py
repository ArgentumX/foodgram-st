# core/validators.py
from django.core.exceptions import ValidationError


def validate_ingredients(ingredients_data, ingredient_model) -> dict:
    if not isinstance(ingredients_data, list):
        raise ValidationError(
            "Ингредиенты должны быть переданы в виде списка.")

    if not ingredients_data:
        raise ValidationError("Нужно указать хотя бы один ингредиент.")

    ingredient_ids = []
    amounts = {}

    for item in ingredients_data:
        if not isinstance(item, dict):
            raise ValidationError("Каждый ингредиент должен быть объектом.")

        try:
            ing_id = int(item["id"])
            amount = int(item["amount"])
        except KeyError as e:
            raise ValidationError(f"В ингредиенте отсутствует или"
                                  f"неверно представлено поле: {e}")

        if amount <= 0:
            raise ValidationError(
                "Количество ингредиента должно быть больше 0.")

        ingredient_ids.append(ing_id)
        amounts[ing_id] = amount

    # Проверка дубликатов
    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise ValidationError("Ингредиенты не должны дублироваться.")

    # Проверка существования
    db_ingredients = ingredient_model.objects.filter(id__in=ingredient_ids)
    if len(db_ingredients) != len(ingredient_ids):
        raise ValidationError("Указан несуществующий ингредиент.")

    return amounts
