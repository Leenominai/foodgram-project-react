from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Конфигурация приложения 'users'.

    Определяет конфигурацию для приложения 'users'.
    Указывает на использование поля 'BigAutoField' для автоматического
    создания первичных ключей по умолчанию.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
