from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """Конфигурация приложения 'recipes'.

    Определяет конфигурацию для приложения 'recipes'.
    Указывает на использование поля 'BigAutoField' для автоматического
    создания первичных ключей по умолчанию.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
