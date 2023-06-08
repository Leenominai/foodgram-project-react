import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """
    Загрузка ингредиентов из JSON-файла в базу данных.

    Принцип работы:
    - Открывает JSON-файл с ингредиентами и считывает данные.
    - Для каждого ингредиента в данных JSON-файла:
        - Извлекает имя и единицу измерения.
        - Создает объект Ingredient с указанными данными.
        - Сохраняет объект Ingredient в базе данных.
    - Возвращает успешное сообщение о загрузке ингредиентов.

    Загрузка происходит через команду Django
    с указанием пути к файлу в аргументе file_path. Например:
    python manage.py load_ingredients ../../static/data/ingredients.json

    """
    help = 'Загружает ингредиенты из JSON-файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к JSON-файлу с ингредиентами'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']

        with open(file_path, 'r', encoding='utf-8') as json_file:
            ingredients_data = json.load(json_file)

        Ingredient.objects.all().delete()

        ingredients_to_create = [
            Ingredient(
                name=ingredient['name'],
                measure_unit=ingredient['measurement_unit']
            )
            for ingredient in ingredients_data
        ]

        Ingredient.objects.bulk_create(ingredients_to_create)

        self.stdout.write(self.style.SUCCESS(
            'Ингредиенты успешно загружены в базу данных.')
        )
