from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from users.models import Subscription, User

from .paginators import RecipePagination
from .utils import Base64ImageField, create_ingredients


class UserSignUpSerializer(UserCreateSerializer):
    """
    Сериализатор для регистрации пользователей.
    """
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class UserGetSerializer(UserSerializer):
    """
    Сериализатор для работы с информацией о пользователях.
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        """
        Получает информацию о том, подписан ли текущий пользователь
        на пользователя `obj`.
        """
        request = self.context.get('request')
        return (request.user.is_authenticated
                and Subscription.objects.filter(
                    user=request.user, author=obj
                ).exists())


class RecipeSmallSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с краткой информацией о рецепте.
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSubscribeRepresentSerializer(UserGetSerializer):
    """
    Сериализатор для предоставления информации о подписках пользователя.
    """
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        """
        Получает информацию о рецептах пользователя `obj`.
        Если передан параметр `recipes_limit`,
        возвращает ограниченное количество рецептов.
        """
        request = self.context.get('request')
        recipes_limit = None
        paginator = RecipePagination()
        paginator.default_limit = (
            recipes_limit if recipes_limit else (
                self.Meta.model.objects.count()
            )
        )
        recipes = obj.recipes.all()
        paginated_recipes = paginator.paginate_queryset(recipes, request)
        return RecipeSmallSerializer(paginated_recipes, many=True,
                                     context={'request': request}).data

    def get_recipes_count(self, obj):
        """
        Получает количество рецептов пользователя `obj`.
        """
        return obj.recipes.count()


class UserSubscribeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписки/отписки от пользователей.
    """
    class Meta:
        model = Subscription
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=(
                    'user',
                    'author'
                ),
                message='Вы уже подписаны на этого пользователя'
            )
        ]

    def validate(self, data):
        """
        Проверяет валидность данных подписки.
        """
        request = self.context.get('request')
        if request.user == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!'
            )
        return data

    def to_representation(self, instance):
        """
        Преобразует объект подписки в сериализованный вид.
        """
        request = self.context.get('request')
        return UserSubscribeRepresentSerializer(
            instance.author, context={'request': request}
        ).data


class TagSerialiser(serializers.ModelSerializer):
    """
    Сериализатор для работы с тегами.
    """
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с ингредиентами.
    """
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения информации об ингредиентах,
    используется при работе с рецептами.
    """
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measure_unit = serializers.CharField(
        source='ingredient.measure_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measure_unit',
            'amount'
        )


class IngredientPostSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления ингредиентов,
    используется при работе с рецептами.
    """
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount'
        )


class RecipeGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения информации о рецепте.
    """
    tags = TagSerialiser(many=True, read_only=True)
    author = UserGetSerializer(read_only=True)
    ingredients = IngredientGetSerializer(many=True, read_only=True,
                                          source='recipeingredients')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'name',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        """
        Проверяет, добавлен ли рецепт `obj`
        в избранное у текущего пользователя.
        """
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and Favorite.objects.filter(
                    user=request.user, recipe=obj
                ).exists())

    def get_is_in_shopping_cart(self, obj):
        """
        Проверяет, добавлен ли рецепт `obj`
        в список покупок у текущего пользователя.
        """
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and ShoppingCart.objects.filter(
                    user=request.user, recipe=obj
                ).exists())


class RecipeCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания нового рецепта.
    """
    ingredients = IngredientPostSerializer(
        many=True, source='recipeingredients'
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        """
        Проверяет валидность данных при создании рецепта.
        """
        ingredients_list = []
        for ingredient in data.get('recipeingredients'):
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError(
                    'Количество не может быть меньше 1'
                )
            ingredients_list.append(ingredient.get('id'))
        if len(set(ingredients_list)) != len(ingredients_list):
            raise serializers.ValidationError(
                'Вы пытаетесь добавить в рецепт два одинаковых ингредиента'
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        """
        Создает новый рецепт и связанные с ним объекты RecipeIngredient.
        """
        request = self.context.get('request')
        ingredients = validated_data.pop('recipeingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        create_ingredients(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Обновляет информацию о рецепте и связанных
        с ним объектах RecipeIngredient.
        """
        ingredients = validated_data.pop('recipeingredients')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        create_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeGetSerializer(
            instance,
            context={'request': request}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с избранными рецептами.
    """
    class Meta:
        model = Favorite
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=(
                    'user',
                    'recipe'
                ),
                message='Рецепт уже добавлен в избранное'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSmallSerializer(
            instance.recipe,
            context={'request': request}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы со списком покупок.
    """
    class Meta:
        model = ShoppingCart
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=(
                    'user',
                    'recipe'
                ),
                message='Рецепт уже добавлен в список покупок'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSmallSerializer(
            instance.recipe,
            context={'request': request}
        ).data
