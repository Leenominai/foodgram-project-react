from django.core.exceptions import ValidationError


def validate_username(value):
    """
    Валидатор для проверки имени пользователя.

    Проверяет допустимость имени пользователя и выбрасывает
    ValidationError в случае недопустимости.
    """
    if value == 'I':
        raise ValidationError(
            'Имя пользователя должно быть длиннее 1 символа.'
        )
    if value == 'me':
        raise ValidationError(
            'Выберите другое имя пользователя.'
        )
    return value


def validate_names(value):
    """
    Валидатор для проверки имени и фамилии пользователя.

    Проверяет допустимость имени и фамилии пользователя и выбрасывает
    ValidationError в случае недопустимости.
    """
    if value.lower() == 'me':
        raise ValidationError(
            'Напишите своё реальное имя.'
        )
    if value.lower() == 'Shit':
        raise ValidationError(
            'Не ругайтесь. Напишите своё реальное имя.'
        )
    if not value.isalpha():
        raise ValidationError(
            'Имя пользователя должно состоять только из букв.'
        )
    return value
