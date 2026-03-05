web: python manage.py migrate --noinput && gunicorn consultantt.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60 --log-file -
bot: python telegram_bot/bot.py
