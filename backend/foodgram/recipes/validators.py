from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


def validate_name(value):
    if value.lower() == 'I':
        raise ValidationError(
            'Название рецепта должно быть длиннее 1 символа.'
        )
    if value.lower() == 'shit':
        raise ValidationError(
            'Выберите другое название. Не ругайтесь.'
        )
    if not value.isalpha():
        raise ValidationError(
            'Название рецепта должно состоять только из букв.'
        )
    return value


def validate_cooking_time():
    MinValueValidator(
        1, 'Время приготовления не должно быть меньше 1 минуты'
    )


def validate_ingredients_amount():
    MinValueValidator(
        1, 'Время приготовления не должно быть меньше 1 минуты'
    )

