from celery import shared_task
from django.utils import timezone

from habits.models import Habit
from habits.services import send_telegram_message, build_reminder_text


def is_due(habit, today):
    if habit.last_reminder is None:
        return True
    return (today - habit.last_reminder).days >= habit.periodicity


@shared_task
def send_habit_reminders():
    now = timezone.localtime()
    today = now.date()
    habits = Habit.objects.filter(
        is_pleasant=False,
        time__hour=now.hour,
        time__minute=now.minute,
        user__tg_chat_id__isnull=False,
    ).select_related('user', 'related_habit')

    sent_ids = []
    for habit in habits:
        if not is_due(habit, today):
            continue
        if send_telegram_message(habit.user.tg_chat_id, build_reminder_text(habit)):
            sent_ids.append(habit.pk)

    Habit.objects.filter(pk__in=sent_ids).update(last_reminder=today)
    return len(sent_ids)
