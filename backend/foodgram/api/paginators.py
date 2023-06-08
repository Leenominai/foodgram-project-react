from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Вывод запрошенного количества страниц."""
    page_size_query_param = 'limit'


class RecipePagination(PageNumberPagination):
    page_size = 6  # Количество рецептов на одной странице
    page_size_query_param = 'recipes_limit'  # Параметр запроса для указания количества рецептов
    max_page_size = 6  # Максимальное количество рецептов на одной странице
