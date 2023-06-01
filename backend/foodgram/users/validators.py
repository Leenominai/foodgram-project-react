import re

from django.core.exceptions import ValidationError


def validate_username(value):
    if value.lower() == 'I':
        raise ValidationError(
            'Имя пользователя должно быть длиннее 1 символа.'
        )
    if value.lower() == 'me':
        raise ValidationError(
            'Выберите другое имя пользователя.'
        )
    if not value.isalpha():
        raise ValidationError(
            'Имя пользователя должно состоять только из букв.'
        )
    return value


def validate_email(value):
    if not bool(re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$', value)):
        raise ValidationError(
            'Некорректный формат электронной почты.'
        )
    return value


def validate_names(value):
    if value.lower() == 'me':
        raise ValidationError(
            'Напиши своё реальное имя.'
        )
    return value
