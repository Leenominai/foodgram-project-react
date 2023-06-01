from rest_framework import filters, permissions, status, views, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from datetime import datetime as dt
from django.shortcuts import HttpResponse, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F, Sum
from djoser.views import UserViewSet as DjoserUserViewSet
from urllib.parse import unquote

from .mixins import AddDelViewMixin
from .paginators import PageLimitPagination
from .variables import UrlQueries, Tuples, incorrect_keys
from .serializers import (UserSerializer, SubscribeSerializer,
                          TagSerializer, IngredientSerializer, RecipeSerializer, RecipeInfoSerializer)
from .permissions import (AdminOrReadOnly, IsAdmin,
                          IsAuthorAdminModeratorOrReadOnly)

from foodgram.settings import DATE_TIME_FORMAT
from users.models import User, Subscription
from recipes.models import (Tag, Ingredient,
                            Recipe, RecipeIngredient,
                            Favorite, ShoppingCart)


class UserViewSet(DjoserUserViewSet, AddDelViewMixin):
    """Подписки на пользователей"""
    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        serializer = SubscribeSerializer(
            data={
                'user': request.user.id,
                'author': author.id
            },
            context={
                'request': request
            }
        )
        serializer.is_valid(
            raise_exception=True
        )
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        if not Subscription.objects.filter(user=request.user,
                                           author=author).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.get(user=request.user.id,
                                 author=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Информация о тегах."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly, )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Информация об ингредиентах."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrReadOnly, )

    def get_queryset(self):
        """Поиск ингредиентов."""
        name = self.request.query_params.get(UrlQueries.SEARCH_INGREDIENT_NAME)
        queryset = self.queryset

        if name:
            if name[0] == '%':
                name = unquote(name)
            else:
                name = name.translate(incorrect_keys)

            name = name.lower()
            start_queryset = list(queryset.filter(name__istartswith=name))
            ingridients_set = set(start_queryset)
            cont_queryset = queryset.filter(name__icontains=name)
            start_queryset.extend(
                [ing for ing in cont_queryset if ing not in ingridients_set]
            )
            queryset = start_queryset

        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """Информация о рецептах.
    Создание нового рецепта, изменение и удаление оных.
    Добавление рецептов в избранное и список покупок.
    Отправка файла со списком рецептов.
    """
    queryset = Recipe.objects.select_related('author')
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorAdminModeratorOrReadOnly,)
    pagination_class = PageLimitPagination
    add_serializer = RecipeInfoSerializer

    def get_queryset(self):
        queryset = self.queryset

        tags: list = self.request.query_params.getlist(UrlQueries.TAGS.value)
        if tags:
            queryset = queryset.filter(
                tags__slug__in=tags).distinct()

        author: str = self.request.query_params.get(UrlQueries.AUTHOR.value)
        if author:
            queryset = queryset.filter(author=author)

        # Следующие фильтры только для авторизованного пользователя
        if self.request.user.is_anonymous:
            return queryset

        is_in_cart: str = self.request.query_params.get(UrlQueries.SHOP_CART)
        if is_in_cart in Tuples.SYMBOL_TRUE_SEARCH.value:
            queryset = queryset.filter(in_carts__user=self.request.user)
        elif is_in_cart in Tuples.SYMBOL_FALSE_SEARCH.value:
            queryset = queryset.exclude(in_carts__user=self.request.user)

        is_favorite: str = self.request.query_params.get(UrlQueries.FAVORITE)
        if is_favorite in Tuples.SYMBOL_TRUE_SEARCH.value:
            queryset = queryset.filter(in_favorites__user=self.request.user)
        if is_favorite in Tuples.SYMBOL_FALSE_SEARCH.value:
            queryset = queryset.exclude(in_favorites__user=self.request.user)

        return queryset

    @action(
        methods=Tuples.ACTION_METHODS,
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Добавление и удаление рецептов из избранного."""
        return self._add_del_obj(pk, Favorite, Q(recipe__id=pk))

    @action(
        methods=Tuples.ACTION_METHODS,
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk) -> Response:
        """Добавление и удаление рецептов из списка покупок."""
        return self._add_del_obj(pk, ShoppingCart, Q(recipe__id=pk))

    @action(methods=('get',), detail=False)
    def download_shopping_cart(self, request) -> Response:
        """Загружает файла со списком покупок."""
        user = self.request.user
        if not user.carts.exists():
            return Response(status=HTTP_400_BAD_REQUEST)

        filename = f'{user.username}_shopping_list.txt'
        shopping_list = [
            f'Список покупок для:\n\n{user.first_name}\n'
            f'{dt.now().strftime(DATE_TIME_FORMAT)}\n'
        ]

        ingredients = Ingredient.objects.filter(
            recipe__recipe__in_carts__user=user
        ).values(
            'name',
            measurement=F('measurement_unit')
        ).annotate(amount=Sum('recipe__amount'))

        for ing in ingredients:
            shopping_list.append(
                f'{ing["name"]}: {ing["amount"]} {ing["measurement"]}'
            )

        shopping_list.append('\nПосчитано в Foodgram')
        shopping_list = '\n'.join(shopping_list)
        response = HttpResponse(
            shopping_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
