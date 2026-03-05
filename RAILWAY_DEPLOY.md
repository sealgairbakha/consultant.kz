# 🚂 Деплой на Railway

## Что нужно заранее

- Аккаунт на [railway.app](https://railway.app) (есть бесплатный план)
- Репозиторий на GitHub с кодом проекта
- Токен Telegram-бота и ваш Telegram ID

---

## Шаг 1 — Залить код на GitHub

```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/ВАШ_НИК/consultantt.git
git push -u origin main
```

> Убедитесь что `.gitignore` содержит `.env` и `db.sqlite3` — они не должны попасть в репозиторий.

---

## Шаг 2 — Создать проект на Railway

1. Зайти на [railway.app](https://railway.app) → **New Project**
2. Выбрать **Deploy from GitHub repo**
3. Выбрать ваш репозиторий `consultantt`
4. Railway автоматически определит Python-проект через `nixpacks.toml`

---

## Шаг 3 — Добавить PostgreSQL

1. В дашборде проекта нажать **+ New** → **Database** → **PostgreSQL**
2. Railway автоматически создаст переменную `DATABASE_URL` и передаст её в ваш сервис
3. Ничего дополнительно делать не нужно — `settings.py` уже настроен

---

## Шаг 4 — Задать переменные окружения

В дашборде сервиса → вкладка **Variables** → добавить:

| Переменная | Значение |
|---|---|
| `SECRET_KEY` | случайная строка 50+ символов |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `your-app.railway.app` |
| `EMAIL_HOST_USER` | ваш gmail |
| `EMAIL_HOST_PASSWORD` | пароль приложения Gmail* |
| `DEFAULT_FROM_EMAIL` | `Consultantt <your@gmail.com>` |
| `WHATSAPP_LINK` | `https://wa.me/7700...` |
| `TELEGRAM_BOT_TOKEN` | токен от @BotFather |
| `TELEGRAM_ADMIN_IDS` | ваш Telegram ID |

> *Пароль приложения Gmail: myaccount.google.com → Безопасность → Двухэтапная аутентификация → Пароли приложений

**Сгенерировать SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## Шаг 5 — Запустить Telegram-бота как отдельный сервис

Railway позволяет запускать несколько процессов в одном проекте:

1. В дашборде проекта → **+ New** → **Empty Service**
2. Подключить тот же GitHub репозиторий
3. В настройках сервиса → **Settings** → **Start Command**:
   ```
   python telegram_bot/bot.py
   ```
4. В этом сервисе также добавить все переменные из Шага 4 (или использовать **Shared Variables**)

---

## Шаг 6 — Проверить деплой

После деплоя Railway выдаст URL вида `https://consultantt-production.up.railway.app`

Проверьте:
- Главная страница открывается
- `/admin` работает (создайте суперпользователя через консоль)
- Telegram-бот отвечает на `/start`

**Создать суперпользователя** (через Railway Shell):
```bash
python manage.py createsuperuser
```

---

## Структура Railway-проекта

```
Railway Project
├── 🌐 Web Service      (Django + gunicorn)
│   └── nixpacks.toml → migrate + collectstatic + gunicorn
├── 🤖 Bot Service      (Telegram-бот)
│   └── Start: python telegram_bot/bot.py
└── 🐘 PostgreSQL       (автоматически → DATABASE_URL)
```

---

## Новые файлы в проекте

| Файл | Назначение |
|---|---|
| `railway.toml` | Конфиг деплоя для Railway |
| `nixpacks.toml` | Команды сборки (install, migrate, collectstatic) |
| `Procfile` | Описание процессов (web + bot) |
