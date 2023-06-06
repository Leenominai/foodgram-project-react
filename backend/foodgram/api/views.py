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

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[AllowAny]
    )
    def favorites(self, request, pk):
        """
        Избранные рецепты пользователя.
        """
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
            queryset = queryset.filter(favorites__user=self.request.user) if is_favorite else queryset.exclude(
                favorites__user=self.request.user)

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
