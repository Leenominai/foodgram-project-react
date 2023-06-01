from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from django.db.models import F
from django.db.transaction import atomic
from typing import List
from drf_extra_fields.fields import Base64ImageField
from .validators import validate_tags, ingredients_validator
from .variables import ingredients_in_recipe
from recipes.models import (Tag, Ingredient,
                            Recipe, RecipeIngredient,
                            Favorite, ShoppingCart)
from users.models import User, Subscription


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор регистрации пользователей."""
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
        )
        read_only_fields = ('is_subscribed', )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and Subscription.objects.filter(
                    user=request.user, author=obj
                ).exists())

    def validate(self, attrs):
        if User.object.filter(
                username=attrs.get('username'),
                email=attrs.get('email')).exists():
            pass
        if (User.object.filter(username=attrs.get('username')).exists()
                and not User.object.filter(email=attrs.get('email')).exists()):
            raise serializers.ValidationError(
                "Пользователь с таким username уже есть."
            )
        if (User.object.filter(email=attrs.get('email')).exists()
                and not User.object.filter(
                    username=attrs.get('username')).exists()):
            raise serializers.ValidationError(
                "Пользователь с таким email уже есть."
            )
        return attrs

    def create(self, validated_data: dict) -> User:
        """Создание нового пользователя."""
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class RecipeInfoSerializer(ModelSerializer):
    """Сериализатор краткой информацией о рецепте."""
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscribeSerializer(UserSerializer):
    """Сериализатор подписок пользователей."""
    recipes = RecipeInfoSerializer(
        many=True,
        read_only=True
    )
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = '__all__',

    def get_is_subscribed(*args):
        """Проверки подписки на пользователя."""
        return True

    def get_recipes_count(self, obj):
        """Количество рецептов для каждого пользователя."""
        return obj.recipes.count()


class TagSerializer(ModelSerializer):
    """Сериализатор для тэгов."""
    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__',

    def validate(self, data):
        """Приводим теги к одному варианту."""
        for attr, value in data.items():
            data[attr] = value.sttrip(' #').upper()
        return data


class IngredientSerializer(ModelSerializer):
    """Сериализатор ингридиентов."""
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__'


class RecipeSerializer(ModelSerializer):
    """Сериализатор рецептов."""
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = UserSerializer(
        read_only=True
    )
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )
        read_only_fields = (
            'is_favorite',
            'is_shopping_cart',
        )

    def get_ingredients(self, recipe):
        """Список ингридиентов для рецепта."""
        ingredients = recipe.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F('recipe__amount')
        )
        return ingredients

    def get_is_favorited(self, recipe):
        """Проверка нахождения рецепта в избранном."""
        user = self.context.get('view').request.user

        if user.is_anonymous:
            return False

        return user.favorites.filter(recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe: Recipe) -> bool:
        """Проверка нахождения рецепта в списке покупок"""
        user = self.context.get('view').request.user

        if user.is_anonymous:
            return False

        return user.carts.filter(recipe=recipe).exists()

    def validate(self, data):
        """Проверка вводных данных для рецепта."""
        tags_ids: List[int] = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')

        if not tags_ids or not ingredients:
            raise ValidationError('Недостаточно данных.')

        validate_tags(tags_ids, Tag)
        ingredients = ingredients_validator(ingredients, Ingredient)

        data.update({
            'tags': tags_ids,
            'ingredients': ingredients,
            'author': self.context.get('request').user
        })
        return data

    @atomic
    def create(self, validated_data: dict) -> Recipe:
        """Создание рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        ingredients_in_recipe(recipe, ingredients)
        return recipe

    @atomic
    def update(self, recipe, validated_data):
        """Обновление рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        for key, value in validated_data.items():
            if hasattr(recipe, key):
                setattr(recipe, key, value)

        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)

        if ingredients:
            recipe.ingredients.clear()
            ingredients_in_recipe(recipe, ingredients)

        recipe.save()
        return recipe
