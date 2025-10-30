from datetime import datetime


def generate_shopping_cart(ingredients, recipes) -> str:
    return '\n'.join([
        'Список покупок',
        f'Дата составления: {datetime.now().strftime("%d.%m.%Y")}',
        '',
        'Продукты:',
        *[
            f"{i}. {ing['ingredient__name'].capitalize()} "
            f"({ing['ingredient__measurement_unit']}) — {ing['total_amount']}"
            for i, ing in enumerate(ingredients, start=1)
        ],
        '',
        'Рецепты:',
        *[
            f"• {recipe['recipe__name']} — "
            f"{recipe['recipe__author__username']}"
            for recipe in recipes
        ],
        '',
        'Приятного приготовления!'
    ])