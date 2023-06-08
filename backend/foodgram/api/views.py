from django.db.models import Sum
from django.shortcuts import HttpResponse, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorAdminModeratorOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeGetSerializer,
                          ShoppingCartSerializer, TagSerialiser,
                          UserSubscribeRepresentSerializer,
                          UserSubscribeSerializer)
from .utils import delete_model_instance, post_model_instance


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

        Права доступа: Авторизованный пользователь

        Принцип работы:
        - При отправке POST-запроса создает подписку на пользователя.
        - При отправке DELETE-запроса удаляет подписку на пользователя.
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
        if request.method == 'DELETE':
            Subscription.objects.filter(
                user=request.user,
                author=author
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response()


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

    Адрес: /api/tags/
    Права доступа: Все пользователи.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerialiser
    permission_classes = (AllowAny, )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Работает с ингредиентами.
    Позволяет получать информацию о доступных ингредиентах.

    Адрес: /api/ingredients/
    Права доступа: Все пользователи.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    pagination_class = None
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter


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
      `/api/recipes/{pk}/shopping_cart/`
      позволяют добавлять и удалять рецепты
      из списка покупок для конкретного рецепта с идентификатором `{pk}`.
    - `download_shopping_cart`: GET запрос по адресу
      `/api/recipes/download_shopping_cart/` позволяет скачать файл CSV со
      списком покупок для текущего пользователя.

    При выполнении действий `favorites` и `shopping_cart`
    необходимо предоставить токен авторизации в заголовке `Authorization`
    в формате `Token <ваш_токен_авторизации>`.

    Параметры фильтрации для списка рецептов:

    - `tags`: список тегов рецептов,
    по которым будет производиться фильтрация.
    - `author`: фильтрация по имени автора рецепта.
    - `shopping_cart`: значение `true` или `false` для фильтрации рецептов в
      списке покупок.
    - `favorite`: значение `true` или `false`
    для фильтрации избранных рецептов для текущего пользователя.

    При выполнении фильтрации по `tags` и `author`
    будет возвращен список рецептов, соответствующих фильтру.
    При выполнении фильтрации по `shopping_cart` и
    `favorite` будет возвращен список рецептов,
    принадлежащих текущему пользователю
    и находящихся в списке покупок или избранном соответственно.

    При выполнении запроса `download_shopping_cart`
    будет сформирован файл CSV со
    списком покупок для текущего пользователя.

    При выполнении запросов на создание и удаление избранного или
    списка покупок будет возвращен статусный код 200 OK
    в случае успешного выполнения запроса или статусный код 400 BAD REQUEST,
    если произошла ошибка или указанный рецепт уже
    находится в избранном или списке покупок.

    http_method_names определяет список HTTP-методов,
    которые представление (ViewSet) будет поддерживать.
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
        Права доступа: Авторизованный пользователь

        Принцип работы:
        - При отправке POST-запроса добавляет рецепт
        в список избранных пользователя.
        - При отправке DELETE-запроса удаляет рецепт
        из списка избранных пользователя.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return post_model_instance(
                request,
                recipe,
                FavoriteSerializer
            )

        if request.method == 'DELETE':
            error_message = 'Данный рецепт отсутствует в вашем избранного.'
            return delete_model_instance(
                request,
                Favorite,
                recipe,
                error_message
            )
        return Response()

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, ]
    )
    def shopping_cart(self, request, pk):
        """
        Добавление и удаление рецептов в корзину покупок.

        Адрес: /api/recipes/{pk}/shopping_cart/
        Права доступа: Авторизованный пользователь

        Принцип работы:
        - При отправке POST-запроса добавляет рецепт
        в корзину покупок пользователя.
        - При отправке DELETE-запроса удаляет рецепт
        из корзины покупок пользователя.
        """
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            return post_model_instance(
                request,
                recipe,
                ShoppingCartSerializer
            )
        if request.method == 'DELETE':
            error_message = 'У вас нет этого рецепта в списке покупок'
            return delete_model_instance(
                request,
                ShoppingCart,
                recipe,
                error_message
            )
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
        Права доступа: Аутентифицированный пользователь

        Принцип работы:
        - Проверяет наличие списка покупок для текущего пользователя.
        - Создает TXT-файл с данными о покупках.
        - Возвращает файл для скачивания.

        Пример ответа:
        - Если список покупок не пуст:
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
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )

        return response
