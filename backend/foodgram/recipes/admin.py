from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)
from .utils import AnyEnums


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Административная панель для модели Tag.

    Отображает список тегов с указанными полями.
    Предоставляет поиск по полям, а также фильтрацию списка.
    Задает значение отображения пустых полей как '-пусто-'.
    """
    list_display = (
        'pk',
        'name',
        'color',
        'slug',
    )
    search_fields = (
        'name',
        'color',
        'slug',
    )
    list_filter = (
        'name',
        'color',
        'slug',
    )
    empty_value_display = AnyEnums.EMPTY_VALUE.value


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Административная панель для модели Ingredient.

    Отображает список ингредиентов с указанными полями.
    Предоставляет поиск по полям, а также фильтрацию списка.
    Задает значение отображения пустых полей как '-пусто-'.
    """
    list_display = (
        'pk',
        'name',
        'measure_unit',
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'name',
    )
    empty_value_display = AnyEnums.EMPTY_VALUE.value


class ShortRecipeIngredient(admin.TabularInline):
    model = RecipeIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Административная панель для модели Recipe.

    Отображает список рецептов с указанными полями.
    Предоставляет поиск по полям, а также фильтрацию списка.
    Задает значение отображения пустых полей как 'empty'.
    Встроенный класс ShortRecipeIngredient отображает
    связанные ингредиенты в рецепте.
    """
    list_display = (
        'pk',
        'name',
        'author',
        'favorites_amount',
    )
    search_fields = (
        'name',
        'author',
        'tags',
    )
    list_filter = (
        'name',
        'author',
        'tags',
    )
    empty_value_display = AnyEnums.EMPTY_VALUE.value
    inlines = [
        ShortRecipeIngredient,
    ]

    def favorites_amount(self, obj):
        return obj.favorites.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """
    Административная панель для модели RecipeIngredient.

    Отображает список связей рецепта и ингредиента с указанными полями.
    Задает значение отображения пустых полей как 'empty'.
    """
    list_display = (
        'pk',
        'recipe',
        'ingredient',
        'amount',
    )
    empty_value_display = AnyEnums.EMPTY_VALUE.value


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Административная панель для модели Favorite.

    Отображает список избранных рецептов с указанными полями.
    Предоставляет поиск по полям.
    Задает значение отображения пустых полей как 'empty'.
    """
    list_display = (
        'pk',
        'user',
        'recipe',
    )
    search_fields = (
        'user',
        'recipe',
    )
    empty_value_display = AnyEnums.EMPTY_VALUE


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """
    Административная панель для модели ShoppingCart.

    Отображает список рецептов в корзине с указанными полями.
    Предоставляет поиск по полям.
    Задает значение отображения пустых полей как 'empty'.
    """
    list_display = (
        'pk',
        'user',
        'recipe',
    )
    search_fields = (
        'user',
        'recipe',
    )
    empty_value_display = AnyEnums.EMPTY_VALUE
