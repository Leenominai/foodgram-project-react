from django.contrib import admin

from .models import Tag, Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart
from .variables import AnyEnums


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
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
    empty_value_display = AnyEnums.EMPTY_SEARCH.value


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
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
    empty_value_display = AnyEnums.EMPTY_SEARCH.value


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'author',
        'image',
        'favorites_count',
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
    empty_value_display = AnyEnums.EMPTY_SEARCH.value
    inlines = (RecipeIngredientInline,)

    def favorites_count(self, obj):
        return obj.favorites.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'recipe',
        'ingredient',
        'amount',
    )
    empty_value_display = AnyEnums.EMPTY_SEARCH.value


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'recipe',
    )
    search_fields = (
        'user',
        'recipe',
    )
    empty_value_display = AnyEnums.EMPTY_SEARCH.value


@admin.register(ShoppingCart)
class ShoppingCart(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'recipe',
    )
    search_fields = (
        'user',
        'recipe',
    )
    empty_value_display = AnyEnums.EMPTY_SEARCH.value
