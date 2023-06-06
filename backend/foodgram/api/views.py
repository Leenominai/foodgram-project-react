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
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.contrib.auth.models import User
from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingCart, RecipeIngredient
from users.models import User, Subscription
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
    Позволяет получать информацию о тегах, используемых в рецептах.
    GET /api/tags/ - Получение списка всех тегов.
    Пример ответа:
    [
        {
            "id": 1,
            "name": "Завтрак",
            "slug": "breakfast"
        },
        ...
    ]
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)


class IngredientViewSet(viewsets.ModelViewSet):
    """
    Работает с ингредиентами.
    Позволяет получать информацию о доступных ингредиентах.
    GET /api/ingredients/ - Получение списка всех ингредиентов.
    Пример ответа:
    [
        {
            "id": 1,
            "name": "Мука",
            "measurement_unit": "г",
            "slug": "flour"
        },
        ...
    ]
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
        Получение списка подписок пользователя.

        Адрес: /api/users/{pk}/subscriptions/
        Метод: GET
        Права доступа: Только аутентифицированные пользователи
        """
        user = self.get_object()
        subscriptions = user.follower.all()
        serializer = SubscribeSerializer(subscriptions, many=True)
        return Response(serializer.data)

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def followers(self, request, pk):
        """
        Получение списка подписчиков пользователя.

        Адрес: /api/users/{pk}/followers/
        Метод: GET
        Права доступа: Только аутентифицированные пользователи
        """
        user = self.get_object()
        followers = user.followers.all()
        serializer = SubscribeSerializer(followers, many=True)
        return Response(serializer.data)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def my(self, request):
        """
        Получение информации о текущем пользователе.

        Адрес: /api/users/my/
        Метод: GET
        Права доступа: Только аутентифицированные пользователи
        """
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk):
        """
        Подписка/отписка на пользователя.

        Адрес: /api/users/{pk}/subscribe/
        Метод: POST, DELETE
        Права доступа: Только аутентифицированные пользователи
        """
        author = get_object_or_404(User, pk=pk)
        user = request.user
        if request.method == 'POST':
            if author != user:
                author.following.get_or_create(user=user)
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(
                    {"detail": "Вы не можете подписаться на себя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif request.method == 'DELETE':
            if author != user:
                author.following.filter(user=user).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"detail": "Вы не можете отписаться от себя."},
                    status=status.HTTP_400_BAD_REQUEST
                )

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

    URL-адреса для действий в этом представлении:

    - `favorites`: POST и DELETE запросы по адресу
      `/api/recipes/{pk}/favorites/` позволяют добавлять и удалять рецепты из
      избранного для конкретного рецепта с идентификатором `{pk}`.
    - `shopping_cart`: POST и DELETE запросы по адресу
      `/api/recipes/{pk}/shopping_cart/` позволяют добавлять и удалять рецепты
      из списка покупок для конкретного рецепта с идентификатором `{pk}`.
    - `download_shopping_cart`: GET запрос по адресу
      `/api/recipes/download_shopping_cart/` позволяет скачать файл CSV со
      списком покупок для текущего пользователя.

    При выполнении действий `favorites` и `shopping_cart` необходимо предоставить
    токен авторизации в заголовке `Authorization` в формате
    `Token <ваш_токен_авторизации>`.

    Параметры фильтрации для списка рецептов:

    - `tags`: список тегов рецептов, по которым будет производиться фильтрация.
    - `author`: фильтрация по имени автора рецепта.
    - `shopping_cart`: значение `true` или `false` для фильтрации рецептов в
      списке покупок.
    - `favorite`: значение `true` или `false` для фильтрации избранных рецептов
      для текущего пользователя.

    При выполнении фильтрации по `tags` и `author` будет возвращен список рецептов,
    соответствующих фильтру. При выполнении фильтрации по `shopping_cart` и
    `favorite` будет возвращен список рецептов, принадлежащих текущему пользователю
    и находящихся в списке покупок или избранном соответственно.

    При выполнении запроса `download_shopping_cart` будет сформирован файл CSV со
    списком покупок для текущего пользователя.

    При выполнении запросов на создание и удаление избранного или списка покупок
    будет возвращен статусный код 200 OK в случае успешного выполнения запроса или
    статусный код 400 BAD REQUEST, если произошла ошибка или указанный рецепт уже
    находится в избранном или списке покупок.
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

        is_favorite = self.request.query_params.get('favorite')
        if is_favorite is not None:
            is_favorite = is_favorite.lower() == 'true'
            queryset = queryset.filter(favorites_received__user=self.request.user) if is_favorite else queryset.exclude(
                favorites_received__user=self.request.user)

        is_in_cart = self.request.query_params.get('shopping_cart')
        if is_in_cart is not None:
            is_in_cart = is_in_cart.lower() == 'true'
            queryset = queryset.filter(in_carts__user=self.request.user) if is_in_cart else queryset.exclude(
                in_carts__user=self.request.user)

        return queryset

    @action(detail=True, methods=['post', 'delete'])
    def favorites(self, request, pk=None):
        """
        Добавление и удаление рецептов из избранного.
        """
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            if created:
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            try:
                favorite = Favorite.objects.get(
                    user=user,
                    recipe=recipe
                )
                favorite.delete()
                return Response(status=status.HTTP_200_OK)
            except Favorite.DoesNotExist:
                return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()

        if request.method == 'POST':
            ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)
            return Response(status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request):
        """
        Загрузка файла со списком покупок.
        """
        user = request.user
        if not ShoppingCart.objects.filter(user=user).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        filename = f'{user.username}_shopping_list.csv'
        shopping_list = []
        shopping_list.append(['Список покупок для:', '', user.first_name])
        shopping_list.append(['Дата:', '', dt.now().strftime("%Y-%m-%d %H:%M:%S")])
        shopping_list.append([])
        shopping_list.append(['Наименование', 'Количество', 'Единицы измерения'])

        ingredients = Ingredient.objects.filter(
            recipeingredients__recipe__carts__user=user
        ).values(
            'name',
            measurement=F('measure_unit'),
        ).annotate(
            amount=Coalesce(Sum('recipeingredients__amount'), 0)
        ).order_by('name').distinct()

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

    @action(detail=True, methods=['get'])
    def user_recipes(self, request, pk=None):
        """
        Получение всех рецептов определенного пользователя.

        Адрес: /api/users/{pk}/user_recipes/
        Метод: GET
        Права доступа: Открытый
        """
        user = get_object_or_404(User, pk=pk)
        recipes = Recipe.objects.filter(author=user)
        page = self.paginate_queryset(recipes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(recipes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def user_favorites(self, request, pk=None):
        """
        Получение избранных рецептов определенного пользователя.

        Адрес: /api/users/{pk}/user_favorites/
        Метод: GET
        Права доступа: Открытый
        """
        user = User.objects.get(pk=pk)
        favorites = Favorite.objects.filter(user=user)
        recipes = [favorite.recipe for favorite in favorites]

        serializer = RecipeSerializer(recipes, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
