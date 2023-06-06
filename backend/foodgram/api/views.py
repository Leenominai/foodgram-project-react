import io
import csv
from datetime import datetime as dt

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F
from django.http import HttpResponse
from django.contrib.auth.models import User
from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingCart, RecipeIngredient
from users.models import User
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    SubscribeSerializer,
    UserSerializer
)
from .permissions import IsAuthorAdminModeratorOrReadOnly, AdminOrReadOnly
from .paginators import PageLimitPagination
from .filters import RecipeFilter


class TagViewSet(ReadOnlyModelViewSet):
    """
    Работает с тегами.

    Изменение и создание тегов разрешено только администраторам.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)


class IngredientViewSet(viewsets.ModelViewSet):
    """
    Представление для просмотра ингредиентов.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrReadOnly,)
    pagination_class = None


class UserViewSet(viewsets.ModelViewSet):
    """
    Представление для работы с информацией о пользователях.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthorAdminModeratorOrReadOnly,)
    pagination_class = None

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request, pk):
        """
        Список подписок пользователя.
        """
        user = self.get_object()
        subscriptions = user.subscriptions.all()
        serializer = SubscribeSerializer(subscriptions, many=True)
        return Response(serializer.data)

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def followers(self, request, pk):
        """
        Список подписчиков пользователя.
        """
        user = self.get_object()
        followers = user.followers.all()
        serializer = SubscribeSerializer(followers, many=True)
        return Response(serializer.data)

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def recipes(self, request, pk):
        """
        Список рецептов пользователя.
        """
        user = self.get_object()
        recipes = user.recipes.all()
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def my(self, request):
        """
        Информация о текущем пользователе.
        """
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def favorites(self, request, pk=None):
        user = self.get_object()
        favorites = user.favorites.all()
        serializer = RecipeSerializer(favorites, many=True)
        return Response(serializer.data)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request):
        """
        Список рецептов в списке покупок пользователя.
        """
        user = request.user
        shopping_cart = user.shopping_cart.all()
        serializer = RecipeSerializer(shopping_cart, many=True)
        return Response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk):
        """
        Подписка/отписка на пользователя.
        """
        author = get_object_or_404(User, pk=pk)
        user = request.user
        if request.method == 'POST':
            if author != user:
                user.subscriptions.get_or_create(author=author)
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(
                    {"detail": "Вы не можете подписаться на себя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif request.method == 'DELETE':
            if author != user:
                user.subscriptions.filter(author=author).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"detail": "Вы не можете отписаться от себя."},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(
        methods=['delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def unsubscribe(self, request, pk):
        """
        Отписка от пользователя.
        """
        return self.subscribe(request, pk)

    @action(
        methods=['post'],
        detail=False,
        permission_classes=[AllowAny]
    )
    def login(self, request):
        """
        Получение JWT-токена для аутентификации пользователя.
        """
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_data = serializer.validated_data
        return Response(token_data)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Представление для работы с информацией о рецептах.
    Включает создание, изменение, удаление рецептов,
    добавление рецептов в избранное и список покупок,
    а также отправку файла со списком рецептов.
    """
    queryset = Recipe.objects.select_related('author')
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorAdminModeratorOrReadOnly,)
    pagination_class = PageLimitPagination
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_queryset(self):
        """
        Возвращает запрос с примененными фильтрами.
        """
        queryset = self.queryset

        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author__username=author)

        if self.request.user.is_anonymous:
            return queryset

        is_in_cart = self.request.query_params.get('shopping_cart')
        if is_in_cart is not None and is_in_cart.lower() == 'true':
            queryset = queryset.filter(in_cart=True)
        elif is_in_cart is not None and is_in_cart.lower() == 'false':
            queryset = queryset.exclude(in_carts__user=self.request.user)

        is_favorite = self.request.query_params.get('favorite')
        if is_favorite is not None and is_favorite.lower() == 'true':
            queryset = queryset.filter(favorites__user=self.request.user)
        elif is_favorite is not None and is_favorite.lower() == 'false':
            queryset = queryset.filter(favorites__user=self.request.user)

        return queryset

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        """
        Добавление и удаление рецептов из избранного.
        """
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            Favorite.objects.get_or_create(user=user, recipe=recipe)
        elif request.method == 'DELETE':
            Favorite.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_200_OK)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request):
        """
        Добавление и удаление рецептов из списка покупок.
        """
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
        elif request.method == 'DELETE':
            ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request):
        """
        Загрузка файла со списком покупок.
        """
        user = request.user
        if not user.carts.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        filename = f'{user.username}_shopping_list.csv'
        shopping_list = []
        shopping_list.append(['Список покупок для:', '', user.first_name])
        shopping_list.append(['Дата:', '', dt.now().strftime("%Y-%m-%d %H:%M:%S")])
        shopping_list.append([])
        shopping_list.append(['Наименование', 'Количество', 'Единицы измерения'])

        ingredients = Ingredient.objects.filter(
            recipe__in_carts__user=user
        ).values(
            'name',
            measurement=F('recipe__amount__measurement_unit')
        ).annotate(amount=Sum('recipe__amount__amount'))

        for ing in ingredients:
            shopping_list.append([ing['name'], ing['amount'], ing['measurement']])

        shopping_list.append(['', '', 'Посчитано в Foodgram'])

        # Создаем объект в памяти для записи CSV
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer, delimiter=',')
        csv_writer.writerows(shopping_list)

        # Создаем HTTPResponse и добавляем заголовки
        response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response

    @action(detail=True, methods=['post'])
    def add_to_favorites(self, request, pk=None):
        recipe = self.get_object()
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if created:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_from_favorites(self, request, pk=None):
        recipe = self.get_object()
        try:
            favorite = Favorite.objects.get(
                user=request.user,
                recipe=recipe
            )
            favorite.delete()
            return Response(status=status.HTTP_200_OK)
        except Favorite.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
