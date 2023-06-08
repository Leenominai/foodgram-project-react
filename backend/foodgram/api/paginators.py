from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Вывод запрошенного количества страниц."""
    page_size_query_param = 'limit'


class RecipePagination(PageNumberPagination):
    """
    Пагинация рецептов.
    page_size - Количество рецептов на одной странице
    page_size_query_param - Параметр запроса для указания количества рецептов
    max_page_size - Максимальное количество рецептов на одной странице
    """

    page_size = 6
    page_size_query_param = 'recipes_limit'
    max_page_size = 6
