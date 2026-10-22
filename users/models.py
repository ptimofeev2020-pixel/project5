from django.contrib.auth.models import AbstractUser
from django.db import models

from users.managers import UserManager


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name='Email')
    tg_chat_id = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='Telegram chat id',
        help_text='ID чата в Telegram для отправки напоминаний',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email
