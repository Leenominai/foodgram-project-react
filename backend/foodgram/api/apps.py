from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Конфигурация приложения 'api'.

    Определяет конфигурацию для приложения 'api'.
    Указывает на использование поля 'BigAutoField' для автоматического
    создания первичных ключей по умолчанию.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
