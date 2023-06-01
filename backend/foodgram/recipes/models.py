from django.db import models

from .variables import Limits
from .validators import validate_name, validate_cooking_time, validate_ingredients_amount

from users.models import User


class Tag(models.Model):
    """Модель Тега для ингредиентов."""
    name = models.CharField(
        'Название тега',
        max_length=Limits.MAX_LEN_TAG.value,
        unique=True,
        help_text='Введите название тега',
        validators=[validate_name, ],
    )
    color = models.CharField(
        'Цвет',
        max_length=Limits.MAX_LEN_COLOR.value,
        unique=True,
        help_text='Выберите цвет',
    )
    slug = models.SlugField(
        'Слаг',
        max_length=Limits.MAX_LEN_TAG.value,
        unique=True,
        help_text='Выберите уникальную название для URL-ссылки на тег',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField(
        'Название ингредиента',
        max_length=Limits.MAX_LEN_INGREDIENT.value,
    )
    measure_unit = models.CharField(
        'Единица измерения',
        max_length=Limits.MAX_LEN_INGREDIENT.value,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель заполнения рецептов."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        'Название рецепта',
        max_length=Limits.MAX_LEN_NAME.value,
        unique=True,
        blank=False,
        null=False,
        help_text='Введите название рецепта',
        validators=[validate_name, ],
    )
    image = models.ImageField(
        'Фото рецепта',
        unique=True,
        blank=False,
        null=False,
        help_text='Добавьте картинку к своему рецепту',
    )
    text = models.TextField(
        'Описание рецепта',
        unique=True,
        blank=False,
        null=False,
        help_text='Введите описание рецепта',
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
        validators=[validate_cooking_time, ],
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель использования ингредиентов в рецепте."""
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
    """Модель избранных рецептов."""
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
        return f'{self.user.username} добавил {self.recipe.name} в избранные рецепты.'


class ShoppingCart(models.Model):
    """Модель списка покупок."""
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
                f'{self.recipe.name} в список покупок')
