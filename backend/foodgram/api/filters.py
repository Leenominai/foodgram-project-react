from django_filters import rest_framework as filters
from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.CharFilter(method='filter_by_tags')
    author = filters.CharFilter(field_name='author__username')

    def filter_by_tags(self, queryset, name, value):
        tags = value.split(',')
        return queryset.filter(tags__slug__in=tags).distinct()

    class Meta:
        model = Recipe
        fields = ['tags', 'author']
