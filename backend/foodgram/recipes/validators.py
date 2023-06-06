import re

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


def validate_name(value):
    """
    Проверка создания некорректного названия рецепта.
    """
    pattern = r'^[A-Za-zА-Яа-я\s.,!?-]+$'
    if not re.match(pattern, value):
        raise ValidationError(
            'Название рецепта должно состоять только из букв английского и '
            'русского алфавитов, а также основных символов (.,!?-).'
        )
    if len(value.strip()) < 2:
        raise ValidationError(
            'Название рецепта должно быть длиной не менее 2 символов.'
        )
    if value.lower() == 'shit':
        raise ValidationError(
            'Выберите другое название. Не ругайтесь.'
        )
    return value


def validate_text(value):
    if len(value.strip()) < 2:
        raise ValidationError(
            'Описание рецепта должно содержать хотя бы 2 символа.'
        )
    return value


def validate_cooking_time(value):
    """
    Время приготовления не должно быть меньше 1 минуты.
    """
    MinValueValidator(1)(value)


def validate_ingredients_amount(value):
    """
    Время приготовления не должно быть меньше 1 минуты.
    """
    MinValueValidator(1)(value)

