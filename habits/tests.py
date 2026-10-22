from datetime import time, timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from habits.models import Habit
from habits.services import send_telegram_message, build_reminder_text
from habits.tasks import send_habit_reminders, is_due
from users.models import User


class HabitBaseTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@mail.ru', password='Pass12345!')
        self.other = User.objects.create_user(email='other@mail.ru', password='Pass12345!')
        self.pleasant = Habit.objects.create(
            user=self.user, place='дома', time=time(20, 0), action='принять ванну',
            is_pleasant=True, duration=60,
        )
        self.habit = Habit.objects.create(
            user=self.user, place='вокруг квартала', time=time(19, 0), action='гулять',
            related_habit=self.pleasant, duration=120,
        )
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('habits:habit-list')

    def detail_url(self, pk):
        return reverse('habits:habit-detail', args=[pk])


class HabitCRUDTestCase(HabitBaseTestCase):
    def test_create(self):
        data = {'place': 'парк', 'time': '07:00', 'action': 'бегать', 'duration': 90, 'reward': 'кофе'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user.pk)
        self.assertEqual(response.data['periodicity'], 1)

    def test_list_paginated(self):
        for i in range(6):
            Habit.objects.create(user=self.user, place='x', time=time(9, i), action=f'д{i}', duration=10)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 8)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data['next'])
        response = self.client.get(self.list_url + '?limit=2&offset=6')
        self.assertEqual(len(response.data['results']), 2)

    def test_retrieve(self):
        response = self.client.get(self.detail_url(self.habit.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'гулять')

    def test_update(self):
        response = self.client.patch(self.detail_url(self.habit.pk), {'place': 'в парке'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.place, 'в парке')

    def test_delete(self):
        response = self.client.delete(self.detail_url(self.habit.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(pk=self.habit.pk).exists())

    def test_other_user_has_no_access(self):
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(self.list_url).data['count'], 0)
        self.assertEqual(self.client.get(self.detail_url(self.habit.pk)).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.patch(self.detail_url(self.habit.pk), {'place': 'x'}).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(self.client.delete(self.detail_url(self.habit.pk)).status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_str(self):
        self.assertEqual(str(self.habit), 'Я буду гулять в 19:00 в вокруг квартала')


class PublicHabitTestCase(HabitBaseTestCase):
    def test_public_list(self):
        Habit.objects.create(
            user=self.other, place='офис', time=time(12, 0), action='пить воду', duration=10, is_public=True,
        )
        response = self.client.get(reverse('habits:public'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['action'], 'пить воду')

    def test_public_habit_not_editable_by_others(self):
        public = Habit.objects.create(
            user=self.other, place='офис', time=time(12, 0), action='пить воду', duration=10, is_public=True,
        )
        self.assertEqual(
            self.client.patch(self.detail_url(public.pk), {'place': 'x'}).status_code, status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(self.client.delete(self.detail_url(public.pk)).status_code, status.HTTP_404_NOT_FOUND)


class HabitValidatorsTestCase(HabitBaseTestCase):
    def post(self, **extra):
        data = {'place': 'парк', 'time': '07:00', 'action': 'бегать', 'duration': 60}
        data.update(extra)
        return self.client.post(self.list_url, data)

    def test_reward_and_related_together(self):
        response = self.post(reward='кофе', related_habit=self.pleasant.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duration_over_120(self):
        response = self.post(duration=121)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duration', response.data)

    def test_related_must_be_pleasant(self):
        response = self.post(related_habit=self.habit.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('related_habit', response.data)

    def test_pleasant_without_reward_or_related(self):
        self.assertEqual(self.post(is_pleasant=True, reward='торт').status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.post(is_pleasant=True, related_habit=self.pleasant.pk).status_code, status.HTTP_400_BAD_REQUEST,
        )

    def test_periodicity_limits(self):
        self.assertEqual(self.post(periodicity=8).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.post(periodicity=0).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.post(periodicity=7).status_code, status.HTTP_201_CREATED)

    def test_update_respects_validators(self):
        response = self.client.patch(self.detail_url(self.habit.pk), {'reward': 'торт'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(TELEGRAM_BOT_TOKEN='test-token')
class TelegramTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='tg@mail.ru', password='Pass12345!', tg_chat_id='12345')
        now = timezone.localtime()
        self.habit = Habit.objects.create(
            user=self.user, place='дома', time=time(now.hour, now.minute), action='медитировать',
            duration=60, reward='чай',
        )

    @patch('habits.services.requests.post')
    def test_send_message(self, mock_post):
        mock_post.return_value.status_code = 200
        self.assertTrue(send_telegram_message('12345', 'текст'))
        args, kwargs = mock_post.call_args
        self.assertIn('/bottest-token/sendMessage', args[0])
        self.assertEqual(kwargs['data'], {'chat_id': '12345', 'text': 'текст'})

    @patch('habits.services.requests.post', side_effect=__import__('requests').RequestException)
    def test_send_message_network_error(self, mock_post):
        self.assertFalse(send_telegram_message('12345', 'текст'))

    @override_settings(TELEGRAM_BOT_TOKEN='')
    def test_send_message_without_token(self):
        self.assertFalse(send_telegram_message('12345', 'текст'))

    def test_reminder_text(self):
        self.assertIn('Вознаграждение: чай', build_reminder_text(self.habit))
        pleasant = Habit.objects.create(
            user=self.user, place='дома', time=time(21, 0), action='читать', is_pleasant=True, duration=60,
        )
        self.habit.reward = None
        self.habit.related_habit = pleasant
        self.assertIn('После этого: читать', build_reminder_text(self.habit))

    @patch('habits.tasks.send_telegram_message', return_value=True)
    def test_task_sends_due_reminders(self, mock_send):
        self.assertEqual(send_habit_reminders(), 1)
        mock_send.assert_called_once()
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.last_reminder, timezone.localdate())
        self.assertEqual(send_habit_reminders(), 0)

    @patch('habits.tasks.send_telegram_message', return_value=True)
    def test_task_respects_periodicity(self, mock_send):
        self.habit.periodicity = 3
        self.habit.last_reminder = timezone.localdate() - timedelta(days=1)
        self.habit.save()
        self.assertEqual(send_habit_reminders(), 0)
        self.habit.last_reminder = timezone.localdate() - timedelta(days=3)
        self.habit.save()
        self.assertEqual(send_habit_reminders(), 1)

    def test_is_due(self):
        today = timezone.localdate()
        self.assertTrue(is_due(self.habit, today))

    def test_beat_schedule(self):
        from django.conf import settings
        self.assertIn('send-habit-reminders', settings.CELERY_BEAT_SCHEDULE)
        self.assertEqual(settings.CELERY_TIMEZONE, settings.TIME_ZONE)


class CorsAndDocsTestCase(APITestCase):
    def test_cors_header(self):
        response = self.client.options(
            reverse('users:register'), HTTP_ORIGIN='http://localhost:3000',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
        )
        self.assertEqual(response['Access-Control-Allow-Origin'], 'http://localhost:3000')

    def test_cors_foreign_origin_denied(self):
        response = self.client.options(
            reverse('users:register'), HTTP_ORIGIN='http://evil.com',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
        )
        self.assertNotIn('Access-Control-Allow-Origin', response)

    def test_docs(self):
        for name in ('schema', 'swagger-ui', 'redoc'):
            self.assertEqual(self.client.get(reverse(name)).status_code, status.HTTP_200_OK)
