from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


def validate_name(value):
    """
    Проверка создания некорректного названия рецепта.
    """
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
    """
    Проверка описания рецепта.
    """
    if len(value.strip()) < 2:
        raise ValidationError(
            'Описание рецепта должно содержать хотя бы 2 символа.'
        )
    return value


def validate_cooking_time(value):
    """
    Проверка времени приготовления рецепта.
    """
    MinValueValidator(1)(value)


def validate_ingredients_amount(value):
    """
    Проверка количества ингредиентов в рецепте.
    """
    MinValueValidator(1)(value)
