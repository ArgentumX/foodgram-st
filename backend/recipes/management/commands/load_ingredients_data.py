import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из JSON-файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='./data/ingredients.json',
            help='Путь к JSON-файлу с ингредиентами'
        )

    def handle(self, *args, **options):
        file_path = Path(options['file'])

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f'Файл {file_path} не найден.'))
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ошибка чтения файла: {e}'))
            return

        valid_ingredients = []

        for item in ingredients_data:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')
            valid_ingredients.append((name, measurement_unit))

        if not valid_ingredients:
            self.stdout.write(
                self.style.SUCCESS('Нет валидных данных для загрузки.')
            )
            return

        with transaction.atomic():
            existing = set(
                Ingredient.objects.values_list('name', 'measurement_unit')
            )

            new_ingredients = [
                Ingredient(name=name, measurement_unit=unit)
                for name, unit in valid_ingredients
                if (name, unit) not in existing
            ]

            created_count = len(new_ingredients)

            if created_count > 0:
                Ingredient.objects.bulk_create(new_ingredients)

        self.stdout.write(
            self.style.SUCCESS(
                f'Загрузка завершена: {created_count} новых ингредиентов.'
            )
        )
