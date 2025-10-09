def generate_shopping_cart(ingredients) -> str:
    lines = ['Список покупок:\n']
    for ing in ingredients:
        lines.append(
            f"{ing['ingredient__name']} ({ing['ingredient__measurement_unit']}) — {ing['total_amount']}"
        )
    lines.append('\nПриятного приготовления!')
    return '\n'.join(lines)
