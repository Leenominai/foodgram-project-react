from django.core.management.base import BaseCommand
from recipes.models import Ingredient
import json


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
    """
    help = 'Загружает ингредиенты из JSON-файла в базу данных'

    def handle(self, *args, **options):
        with open('../../static/data/ingredients.json', 'r', encoding='utf-8') as json_file:
            ingredients_data = json.load(json_file)

        Ingredient.objects.all().delete()

        for ingredient in ingredients_data:
            name = ingredient['name']
            measurement_unit = ingredient['measurement_unit']
            Ingredient.objects.create(name=name, measure_unit=measurement_unit)

        self.stdout.write(self.style.SUCCESS('Ингредиенты успешно загружены в базу данных.'))
