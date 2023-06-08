import json

from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import HttpResponse, get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorAdminModeratorOrReadOnly
from .serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeGetSerializer,
    ShoppingCartSerializer,
    TagSerialiser,
    UserSubscribeRepresentSerializer,
    UserSubscribeSerializer
)
from .variables import create_model_instance, delete_model_instance
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart
)
from users.models import User, Subscription


class UserSubscribeViewSet(viewsets.GenericViewSet):
    """
    Создание/удаление подписки на пользователя.

    Позволяет создавать и удалять подписку на пользователя.
    """
    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete']
    )
    def subscribe(self, request, pk=None):
        """
        Создание/удаление подписки на пользователя.

        Методы: POST, DELETE
        Права доступа: Авторизованный пользователь

        Принцип работы:
        - При отправке POST-запроса создает подписку на пользователя.
        - При отправке DELETE-запроса удаляет подписку на пользователя.

        Пример ответа при успешном создании:
        HTTP 201 CREATED

        Пример ответа при успешном удалении:
        HTTP 204 NO CONTENT

        Пример ответа при попытке удалить несуществующую подписку:
        HTTP 400 BAD REQUEST
        """
        author = get_object_or_404(User, id=pk)
        if request.method == 'POST':
            serializer = UserSubscribeSerializer(
                data={'user': request.user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not Subscription.objects.filter(user=request.user, author=author).exists():
                return Response(
                    {'errors': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.get(user=request.user.id, author=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class UserSubscriptionsViewSet(mixins.ListModelMixin,
                               viewsets.GenericViewSet):
    """
    Получение списка всех подписок на пользователей.
    """
    serializer_class = UserSubscribeRepresentSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
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
    serializer_class = TagSerialiser
    permission_classes = (AllowAny, )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
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
    permission_classes = (AllowAny, )
    pagination_class = None
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthorAdminModeratorOrReadOnly]
    )
    def load_ingredients(self, request):
        """
        Загрузка ингредиентов из JSON-файла в базу данных.

        Адрес: /api/ingredients/load_ingredients/
        Метод: GET
        Права доступа: Автор, администратор или модератор

        Принцип работы:
        - Открывает JSON-файл с ингредиентами и считывает данные.
        - Для каждого ингредиента в данных JSON-файла:
            - Извлекает имя и единицу измерения.
            - Создает объект Ingredient с указанными данными.
            - Сохраняет объект Ingredient в базе данных.
        - Возвращает успешное сообщение о загрузке ингредиентов.

        Пример ответа:
        {
            "message": "Все ингредиенты успешно загружены."
        }
        """
        with open('../../static/data/ingredients.json', 'r', encoding='utf-8') as json_file:
            ingredients_data = json.load(json_file)

        for ingredient in ingredients_data:
            name = ingredient['name']
            measurement_unit = ingredient['measurement_unit']

            Ingredient.objects.create(name=name, measure_unit=measurement_unit)

        return Response({'message': 'Все ингредиенты успешно загружены.'}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['delete'],
        permission_classes=[IsAuthorAdminModeratorOrReadOnly]
    )
    def delete_all(self, request):
        """
        Удаление всех ингредиентов из базы данных.

        Адрес: /api/ingredients/delete_all/
        Метод: DELETE
        Права доступа: Автор, администратор или модератор

        Принцип работы:
        - Удаляет все объекты Ingredient из базы данных.
        - Возвращает успешное сообщение об удалении всех ингредиентов.

        Пример ответа:
        {
            "message": "Все ингредиенты успешно удалены."
        }
        """
        Ingredient.objects.all().delete()
        return Response({'message': 'Все ингредиенты успешно удалены.'})


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
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorAdminModeratorOrReadOnly, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, ]
    )
    def favorite(self, request, pk):
        """
        Добавление и удаление рецептов из избранного.

        Адрес: /api/recipes/{pk}/favorite/
        Методы: POST, DELETE
        Права доступа: Авторизованный пользователь

        Принцип работы:
        - При отправке POST-запроса добавляет рецепт в список избранных пользователя.
        - При отправке DELETE-запроса удаляет рецепт из списка избранных пользователя.

        Пример ответа при успешном добавлении:
        HTTP 200 OK

        Пример ответа при попытке повторного добавления:
        HTTP 400 BAD REQUEST

        Пример ответа при успешном удалении:
        HTTP 200 OK

        Пример ответа при отсутствии рецепта в списке избранных:
        HTTP 204 NO CONTENT
        """
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            response = create_model_instance(
                request,
                recipe,
                FavoriteSerializer
            )
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            else:
                return response

        if request.method == 'DELETE':
            error_message = 'Данный рецепт отсутствует в вашем избранного.'
            response = delete_model_instance(
                request,
                Favorite,
                recipe,
                error_message
            )
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            else:
                return response

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, ]
    )
    def shopping_cart(self, request, pk):
        """
        Добавление и удаление рецептов в корзину покупок.

        Адрес: /api/recipes/{pk}/shopping_cart/
        Методы: POST, DELETE
        Права доступа: Авторизованный пользователь

        Принцип работы:
        - При отправке POST-запроса добавляет рецепт в корзину покупок пользователя.
        - При отправке DELETE-запроса удаляет рецепт из корзины покупок пользователя.

        Пример ответа при успешном добавлении:
        HTTP 200 OK

        Пример ответа при успешном удалении:
        HTTP 204 NO CONTENT
        """
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            response = create_model_instance(
                request,
                recipe,
                ShoppingCartSerializer
            )
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            else:
                return response

        if request.method == 'DELETE':
            error_message = 'У вас нет этого рецепта в списке покупок'
            response = delete_model_instance(
                request,
                ShoppingCart,
                recipe,
                error_message
            )
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            else:
                return response

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, ]
    )
    def download_shopping_cart(self, request):
        """
        Загрузка файла со списком покупок.
        Ингредиенты не дублируются, их кол-во суммируется.

        Адрес: /api/download_shopping_cart/
        Метод: GET
        Права доступа: Аутентифицированный пользователь

        Принцип работы:
        - Проверяет наличие списка покупок для текущего пользователя.
        - Создает TXT-файл с данными о покупках.
        - Возвращает файл для скачивания.

        Пример ответа:
        - Если список покупок пуст:
          HTTP 400 Bad Request
        - Если список покупок не пуст:
          HTTP 200 OK
          Файл TXT с данными о покупках для скачивания.
        """
        ingredients = RecipeIngredient.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measure_unit'
        ).annotate(ingredient_amount=Sum('amount'))

        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measure_unit']
            amount = ingredient['ingredient_amount']
            shopping_list.append(f'\n{name} - {amount}, {unit}')

        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'

        return response
