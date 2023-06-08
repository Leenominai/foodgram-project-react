from django.db import models

from .validators import (
    validate_name,
    validate_cooking_time,
    validate_ingredients_amount,
    validate_text
)
from users.models import User


class Tag(models.Model):
    """
    Модель для тега рецепта.

    Содержит название, цвет и слаг
    (уникальное название для URL-ссылки на тег).
    """
    name = models.CharField(
        'Название',
        max_length=200,
        unique=True,
        help_text='Введите название тега',
        validators=[validate_name, ],
    )
    color = models.CharField(
        'Цвет',
        max_length=7,
        unique=True,
        help_text='Выберите цвет',
    )
    slug = models.SlugField(
        'Слаг',
        max_length=200,
        unique=True,
        help_text='Выберите уникальное название для URL-ссылки на тег',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """
    Модель для ингредиента рецепта.

    Содержит название и единицу измерения ингредиента.
    """
    name = models.CharField(
        'Название',
        max_length=200,
    )
    measure_unit = models.CharField(
        'Единица измерения',
        max_length=200,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """
    Модель для рецепта.

    Каждый рецепт имеет автора, название, картинку, описание,
    список ингредиентов, теги и время приготовления.
    """
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        'Название',
        max_length=200,
        help_text='Введите название рецепта',
        validators=[validate_name, ],
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
        blank=True,
        help_text='Добавьте картинку к своему рецепту',
    )
    text = models.TextField(
        'Описание',
        help_text='Введите описание рецепта',
        validators=[validate_text, ],
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        help_text='Выберите время в минутах',
        validators=[validate_cooking_time, ],
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Модель для ингредиента в рецепте.

    Связывает рецепт с ингредиентом и указывает количество ингредиента.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipeingredients',
        verbose_name='Рецепт'

    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipeingredients',
        verbose_name='Ингредиент'
    )
    amount = models.IntegerField(
        'Количество',
        validators=[validate_ingredients_amount, ],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'


class Favorite(models.Model):
    """
    Модель для избранного.

    Связывает пользователя с избранным рецептом.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_favorite'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user.username} добавил {self.recipe.name} в избраннные рецепты.'


class ShoppingCart(models.Model):
    """
    Модель для списка покупок.

    Связывает пользователя с рецептом в списке покупок.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='Рецепт'
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_cart'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return (f'{self.user.username} добавил'
                f'{self.recipe.name} в список покупок.')