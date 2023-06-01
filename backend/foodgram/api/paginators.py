from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Вывод запрошенного количества страниц."""
    page_size_query_param = 'limit'
