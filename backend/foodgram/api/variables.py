from enum import Enum

from recipes.models import RecipeIngredient


def ingredients_in_recipe(recipe, ingredients):
    """Ингредиенты в рецепте."""
    obj = []

    for ingredient, amount in ingredients.values():
        obj.append(RecipeIngredient(
            recipe=recipe,
            ingredients=ingredient,
            amount=amount
        ))

    RecipeIngredient.objects.bulk_create(obj)


class UrlQueries(str, Enum):
    # Поиск ингредиентов
    SEARCH_INGREDIENT_NAME = 'name'
    # Параметр для поиска объектов в списке "избранное"
    FAVORITE = 'is_favorited'
    # Параметр для поиска объектов в списке "покупки"
    SHOP_CART = 'is_in_shopping_cart'
    # Параметр для поиска объектов по автору
    AUTHOR = 'author'
    # Параметр для поиска объектов по тэгам
    TAGS = 'tags'


class Tuples(tuple, Enum):
    # Размер сохраняемого изображения рецепта
    RECIPE_IMAGE_SIZE = 500, 300
    # Поиск объектов только с переданным параметром.
    # Например только в избранном: `is_favorited=1`
    SYMBOL_TRUE_SEARCH = '1', 'true'
    # Поиск объектов не содержащих переданный параметр.
    # Например только не избранное: `is_favorited=0`
    SYMBOL_FALSE_SEARCH = '0', 'false'
    ADD_METHODS = 'GET', 'POST'
    DEL_METHODS = 'DELETE',
    ACTION_METHODS = 'GET', 'POST', 'DELETE'
    UPDATE_METHODS = 'PUT', 'PATCH'


# Сопоставление RU и ENG раскладки на клавиатуре.
incorrect_keys = str.maketrans(
    'qwertyuiop[]asdfghjkl;\'zxcvbnm,./',
    'йцукенгшщзхъфывапролджэячсмитьбю.'
)