# 🤖 Telegram-бот для подтверждения оплаты

## Как это работает

```
Клиент оформляет заказ на сайте
        ↓
Бот присылает уведомление администратору с кнопками
        ↓
Администратор нажимает ✅ "Подтвердить оплату"
        ↓
Система автоматически отправляет документ на email клиента
```

---

## Шаг 1 — Создать бота в Telegram

1. Открыть [@BotFather](https://t.me/BotFather) в Telegram
2. Отправить `/newbot`
3. Придумать имя и username (например `ConsultanttShopBot`)
4. Скопировать **токен** вида `1234567890:AAxxxxxx...`

---

## Шаг 2 — Узнать свой Telegram ID

1. Открыть [@userinfobot](https://t.me/userinfobot)
2. Написать `/start`
3. Скопировать число из поля **Id** (например `123456789`)

Если администраторов несколько — добавьте все ID через запятую.

---

## Шаг 3 — Добавить переменные в .env

Открыть файл `.env` и добавить:

```env
TELEGRAM_BOT_TOKEN=1234567890:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_ADMIN_IDS=123456789
```

Для нескольких администраторов:
```env
TELEGRAM_ADMIN_IDS=123456789,987654321
```

---

## Шаг 4 — Установить зависимости

```bash
pip install -r requirements.txt
```

---

## Шаг 5 — Запустить бота

Бот запускается **отдельным процессом** — параллельно с Django:

```bash
# В одном терминале — Django
python manage.py runserver

# В другом терминале — Telegram-бот
python telegram_bot/bot.py
```

### На сервере (через systemd)

Создать файл `/etc/systemd/system/consultantt-bot.service`:

```ini
[Unit]
Description=Consultantt Telegram Bot
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/consultantt
ExecStart=/path/to/venv/bin/python telegram_bot/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable consultantt-bot
systemctl start consultantt-bot
```

---

## Команды бота

| Команда | Описание |
|---|---|
| `/start` | Приветствие и список команд |
| `/orders` | Все заказы, ожидающие оплаты |
| `/order 42` | Информация о конкретном заказе |

---

## Что происходит при нажатии кнопок

**✅ Подтвердить оплату:**
- Статус заказа → `sent`
- Документ отправляется на email клиента
- Бот показывает подтверждение

**❌ Отменить заказ:**
- Статус заказа → `cancelled`
- Email клиенту не отправляется

---

## Структура новых файлов

```
consultantt/
├── telegram_bot/
│   ├── __init__.py
│   ├── bot.py          ← основной процесс бота (polling)
│   └── notifier.py     ← отправка уведомлений из Django
└── shop/
    └── signals.py      ← обновлён: уведомляет бот при новом заказе
```
