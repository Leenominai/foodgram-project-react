from django.contrib import admin

from .models import Subscription, User
from .utils import AnyEnums


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Административная панель для модели User.

    Отображает список пользователей с указанными полями.
    Предоставляет поиск по полям, а также фильтрацию списка.
    Задает значение отображения пустых полей как '-пусто-'.
    """
    list_display = (
        'pk',
        'username',
        'email',
        'first_name',
        'last_name',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    list_filter = (
        'username',
        'email',
    )
    empty_value_display = AnyEnums.EMPTY_VALUE.value


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """
    Административная панель для модели User.

    Отображает список пользователей с указанными полями.
    Предоставляет поиск по полям, а также фильтрацию списка.
    Задает значение отображения пустых полей как '-пусто-'.
    """
    list_display = (
        'pk',
        'user',
        'author',
    )
    search_fields = (
        'user',
        'author',
    )
    list_filter = (
        'user',
        'author',
    )
    empty_value_display = AnyEnums.EMPTY_VALUE.value
