from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class UserAuthTestCase(APITestCase):
    def test_register(self):
        response = self.client.post(
            reverse('users:register'), {'email': 'new@mail.ru', 'password': 'Pass12345!', 'tg_chat_id': '111'},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        self.assertTrue(User.objects.get(email='new@mail.ru').check_password('Pass12345!'))

    def test_register_duplicate(self):
        User.objects.create_user(email='dup@mail.ru', password='Pass12345!')
        response = self.client.post(reverse('users:register'), {'email': 'dup@mail.ru', 'password': 'Pass12345!'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_and_refresh(self):
        User.objects.create_user(email='log@mail.ru', password='Pass12345!')
        response = self.client.post(reverse('users:login'), {'email': 'log@mail.ru', 'password': 'Pass12345!'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh = self.client.post(reverse('users:token_refresh'), {'refresh': response.data['refresh']})
        self.assertEqual(refresh.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh.data)

    def test_login_wrong_password(self):
        User.objects.create_user(email='w@mail.ru', password='Pass12345!')
        response = self.client.post(reverse('users:login'), {'email': 'w@mail.ru', 'password': 'bad'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_superuser_and_str(self):
        admin = User.objects.create_superuser(email='admin@mail.ru', password='Pass12345!')
        self.assertTrue(admin.is_superuser)
        self.assertEqual(str(admin), 'admin@mail.ru')
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='x')
