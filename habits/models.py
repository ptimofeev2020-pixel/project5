from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='habits', verbose_name='Пользователь',
    )
    place = models.CharField(max_length=255, verbose_name='Место')
    time = models.TimeField(verbose_name='Время')
    action = models.CharField(max_length=255, verbose_name='Действие')
    is_pleasant = models.BooleanField(default=False, verbose_name='Признак приятной привычки')
    related_habit = models.ForeignKey(
        'self', on_delete=models.SET_NULL, blank=True, null=True,
        related_name='linked_habits', verbose_name='Связанная привычка',
    )
    periodicity = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        verbose_name='Периодичность (в днях)',
    )
    reward = models.CharField(max_length=255, blank=True, null=True, verbose_name='Вознаграждение')
    duration = models.PositiveIntegerField(
        validators=[MaxValueValidator(120)],
        verbose_name='Время на выполнение (в секундах)',
    )
    is_public = models.BooleanField(default=False, verbose_name='Признак публичности')
    last_reminder = models.DateField(blank=True, null=True, verbose_name='Дата последнего напоминания')

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'
        ordering = ['id']

    def __str__(self):
        return f'Я буду {self.action} в {self.time:%H:%M} в {self.place}'
