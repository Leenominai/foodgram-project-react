from django.core.exceptions import ValidationError


def validate_tags(tags_ids, Tag):
    """Проверяет наличие тэгов."""
    exists_tags = Tag.objects.filter(id__in=tags_ids)
    if len(exists_tags) != len(tags_ids):
        raise ValidationError('Указан несуществующий тэг')


def ingredients_validator(ingredients, Ingredient):
    """Проверка списка ингридиентов."""
    ingredients_validate = {}
    for ing in ingredients:
        if not (isinstance(ing['amount'], int) or ing['amount'].isdigit()):
            raise ValidationError('Неправильное количество ингидиента')

        amount = ingredients_validate.get(ing['id'], 0) + int(ing['amount'])
        if amount <= 0:
            raise ValidationError('Неправильное количество ингридиента')

        ingredients_validate[ing['id']] = amount

    if not ingredients_validate:
        raise ValidationError('Неправильные ингидиенты')

    ingredients_db = Ingredient.objects.filter(pk__in=ingredients_validate.keys())
    if not ingredients_db:
        raise ValidationError('Неправильные ингидиенты')

    for ing in ingredients_db:
        ingredients_validate[ing.pk] = (ing, ingredients_validate[ing.pk])

    return ingredients_validate
