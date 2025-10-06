def generate_shopping_cart_txt(ingredients):
    """Генерирует TXT-содержимое списка покупок."""
    lines = ['Список покупок:\n']
    for ing in ingredients:
        lines.append(
            f"{ing['ingredient__name']} ({ing['ingredient__measurement_unit']}) — {ing['total_amount']}"
        )
    lines.append('\nПриятного приготовления!')
    return '\n'.join(lines)
