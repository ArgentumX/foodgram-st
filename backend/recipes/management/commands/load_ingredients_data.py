import json
from pathlib import Path
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из ingredients.json'

    def handle(self, *args, **options):
        file_path = Path('./data/ingredients.json')

        if not file_path.exists():
            self.stderr.write(
                self.style.ERROR(f'Файл {file_path} не найден.')
            )
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Ошибка чтения файла: {e}')
            )
            return

        created_count = 0
        skipped_count = 0

        for item in ingredients_data:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')

            if not name or not measurement_unit:
                self.stderr.write(
                    self.style.WARNING(f'Пропущена запись: {item}')
                )
                skipped_count += 1
                continue

            _, created = Ingredient.objects.get_or_create(
                name=name,
                measurement_unit=measurement_unit
            )

            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Загрузка завершена: {created_count} новых ингредиентов. '
                f'{skipped_count} записей пропущено из-за испорченных данных.'
            )
        )
