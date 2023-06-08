from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """
    Удаление всех ингредиентов из базы данных.

    Принцип работы:
    - Удаляет все объекты Ingredient из базы данных.
    - Возвращает успешное сообщение об удалении всех ингредиентов.
    """
    help = 'Удаляет все ингредиенты из базы данных'

    def handle(self, *args, **options):
        Ingredient.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            'Все ингредиенты успешно удалены из базы данных.')
        )
