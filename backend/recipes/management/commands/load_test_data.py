from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Импортирует продукты и связанные данные из фикстуры test.json'

    def handle(self, *args, **options):
        fixture_path = 'fixtures/test_data.json'
        try:
            call_command('loaddata', fixture_path, verbosity=2)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Данные успешно загружены из {fixture_path}'
                )
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Ошибка при загрузке фикстуры: {e}')
            )
