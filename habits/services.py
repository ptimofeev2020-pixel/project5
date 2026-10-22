import requests
from django.conf import settings


def send_telegram_message(chat_id, text):
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    url = f'{settings.TELEGRAM_API_URL}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage'
    try:
        response = requests.post(url, data={'chat_id': chat_id, 'text': text}, timeout=10)
    except requests.RequestException:
        return False
    return response.status_code == 200


def build_reminder_text(habit):
    text = f'Напоминание: я буду {habit.action} в {habit.time:%H:%M} в {habit.place}.'
    if habit.related_habit:
        text += f' После этого: {habit.related_habit.action}.'
    elif habit.reward:
        text += f' Вознаграждение: {habit.reward}.'
    return text
