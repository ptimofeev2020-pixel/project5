# Проект 5. Трекер привычек

Бэкенд SPA-приложения для трекинга полезных привычек по книге Джеймса Клира «Атомные привычки».
Привычка формулируется так: «я буду [ДЕЙСТВИЕ] в [ВРЕМЯ] в [МЕСТО]».

## Стек

Python, Django 5.2, Django REST Framework, Simple JWT, PostgreSQL, Celery, Redis, Telegram Bot API,
django-cors-headers, drf-spectacular.

## Модель «Привычка»

Пользователь, место, время, действие, признак приятной привычки, связанная привычка, периодичность
(в днях, по умолчанию 1), вознаграждение, время на выполнение (в секундах), признак публичности.

## Валидаторы

- нельзя одновременно указать вознаграждение и связанную привычку;
- время на выполнение — не больше 120 секунд;
- связанной может быть только приятная привычка;
- у приятной привычки не может быть вознаграждения или связанной привычки;
- выполнять привычку нужно не реже раза в 7 дней (периодичность от 1 до 7).

## Эндпоинты

| Метод | Адрес | Описание |
|---|---|---|
| POST | `/users/register/` | Регистрация |
| POST | `/users/login/` | Авторизация, пара access/refresh токенов |
| POST | `/users/token/refresh/` | Обновление access-токена |
| GET | `/habits/` | Свои привычки, пагинация по 5 (`limit`/`offset`) |
| POST | `/habits/` | Создание привычки |
| GET, PUT, PATCH, DELETE | `/habits/<id>/` | Просмотр, редактирование, удаление своей привычки |
| GET | `/habits/public/` | Публичные привычки (только чтение) |

Документация: `/api/docs/` (Swagger), `/api/redoc/`, `/api/schema/`.

## Права доступа

Все эндпоинты, кроме регистрации и авторизации, доступны только с JWT-токеном.
Пользователь работает по CRUD только со своими привычками. Публичные привычки других
пользователей видны в списке `/habits/public/`, но изменить или удалить их нельзя.

## Telegram-напоминания

1. Создайте бота у [@BotFather](https://t.me/BotFather) и запишите токен в `TELEGRAM_BOT_TOKEN`.
2. Узнайте свой chat id (например, через [@userinfobot](https://t.me/userinfobot)) и укажите его в поле
   `tg_chat_id` при регистрации.
3. Напишите своему боту `/start`, иначе Telegram не даст ему отправлять вам сообщения.

Celery-beat каждую минуту запускает задачу `habits.tasks.send_habit_reminders`: она находит полезные
привычки, время которых наступило, учитывает периодичность и отправляет напоминание в Telegram.

## Установка и запуск

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Нужны запущенные PostgreSQL и Redis. В отдельных терминалах:

```
celery -A config worker -l info -P solo
celery -A config beat -l info
```

(`-P solo` нужен на Windows.)

## Тесты и стиль кода

```
coverage run --source='.' manage.py test
coverage report
flake8
```

Покрытие — 99% (`coverage_report.txt`), flake8 замечаний не выдаёт.
