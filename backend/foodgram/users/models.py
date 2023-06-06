from django.contrib.auth.models import AbstractUser
from django.db import models

from .variables import Limits
from .validators import validate_username, validate_email, validate_names


class User(AbstractUser):
    """Регистрация пользователей Foodgram.
    Все поля обязательны для заполнения.
    """
    username = models.CharField(
        'Имя пользователя',
        max_length=Limits.MAX_LEN_USERNAME,
        unique=True,
        blank=False,
        null=False,
        help_text='Введите имя пользователя',
        validators=[validate_username, ],
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=Limits.MAX_LEN_EMAIL,
        unique=True,
        blank=False,
        null=False,
        help_text='Введите электронную почту',
        validators=[validate_email, ],
    )
    first_name = models.CharField(
        'Имя',
        max_length=Limits.MAX_LEN_NAMES,
        blank=False,
        null=False,
        help_text='Введите своё имя',
        validators=[validate_names, ],
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=Limits.MAX_LEN_NAMES,
        blank=False,
        null=False,
        help_text='Введите свою фамилию',
        validators=[validate_names, ],
    )
    password = models.CharField(
        'Пароль',
        max_length=Limits.MAX_LEN_PASSWORD,
        blank=False,
        null=False,
        help_text='Придумайте пароль',
    )
    is_active = models.BooleanField(
        verbose_name='Пользователь активировен',
        default=True,
    )

    class Meta:
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_name_email'
            )
        ]

    def __str__(self):
        return self.username


class Subscription(models.Model):
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
            name='user_to_author_follow',
            )
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
