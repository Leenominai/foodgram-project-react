from django.contrib import admin

from .models import User, Subscription
from .variables import AnyEnums


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
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
    empty_value_display = AnyEnums.EMPTY_SEARCH.value


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
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
    empty_value_display = AnyEnums.EMPTY_SEARCH.value
