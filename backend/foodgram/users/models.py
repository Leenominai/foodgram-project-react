from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import EmailValidator

from .validators import validate_username, validate_names


class User(AbstractUser):
    """
    Модель пользователя.

    Содержит поля для хранения данных пользователя.
    """
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
        blank=False,
        null=False,
        help_text='Введите электронную почту',
        validators=[
            EmailValidator(
                message='Некорректный формат электронной почты.'
            )
        ],
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
        blank=False,
        null=False,
        help_text='Введите имя пользователя',
        validators=[validate_username, ],
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
        blank=False,
        null=False,
        help_text='Введите своё имя',
        validators=[validate_names, ],
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
        blank=False,
        null=False,
        help_text = 'Введите свою фамилию',
        validators = [validate_names, ],
    )
    password = models.CharField(
        'Пароль',
        max_length=150,
        blank=False,
        null=False,
        help_text='Придумайте пароль',
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """
    Модель подписки.

    Представляет связь между пользователем и автором.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
