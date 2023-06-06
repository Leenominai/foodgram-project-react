from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from django.db.transaction import atomic
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
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
        extra_kwargs = {
            'password': {'write_only': True},
        }
        read_only_fields = ('is_subscribed', )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and Subscription.objects.filter(
                    user=request.user, author=obj
                ).exists())

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if User.objects.filter(username=attrs.get('username')).exists():
            raise serializers.ValidationError("Пользователь с таким username уже есть.")
        if User.objects.filter(email=attrs.get('email')).exists():
            raise serializers.ValidationError("Пользователь с таким email уже есть.")
        return attrs

    def create(self, validated_data: dict) -> User:
        """Создание нового пользователя."""
        validated_data['password'] = make_password(validated_data['password'])
        user = User.objects.create(**validated_data)
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
        read_only_fields = ('__all__',)

    def get_is_subscribed(self, obj):
        """Проверки подписки на пользователя."""
        user = self.context['request'].user
        return user.following.filter(author=obj).exists()

    def get_recipes_count(self, obj):
        """Количество рецептов для каждого пользователя."""
        return obj.recipes.count()


class TagSerializer(ModelSerializer):
    """Сериализатор для тэгов."""
    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = ('__all__',)

    def validate(self, data):
        """Приводим теги к одному варианту."""
        for attr, value in data.items():
            data[attr] = value.strip(' #').upper()
        return data


class IngredientSerializer(ModelSerializer):
    """Сериализатор ингридиентов."""
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = ('__all__',)


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
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_ingredients(self, recipe):
        """Список ингридиентов для рецепта."""
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
        ingredients = recipe_ingredients.values(
            'ingredient__id',
            'ingredient__name',
            'ingredient__measure_unit',
            'amount'
        )
        return ingredients

    def get_is_favorited(self, recipe: Recipe) -> bool:
        user = self.context.get('view').request.user

        if user.is_authenticated:
            return user.favorites_received.filter(recipe=recipe).exists()

        return False

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
