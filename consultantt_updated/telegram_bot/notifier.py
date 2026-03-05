"""
Утилита для отправки уведомлений в Telegram-бот администраторам.
Используется из Django signals при создании нового заказа.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_ADMIN_IDS_RAW = os.environ.get('TELEGRAM_ADMIN_IDS', '')
TELEGRAM_ADMIN_IDS = [
    int(i.strip()) for i in TELEGRAM_ADMIN_IDS_RAW.split(',') if i.strip()
]


def send_telegram_notification(order) -> None:
    """Отправить уведомление о новом заказе всем администраторам."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ADMIN_IDS:
        logger.warning('Telegram не настроен — уведомление не отправлено.')
        return

    payment_emoji = '💳' if order.payment_method == 'kaspi' else '🏦'
    text = (
        f'🛒 *Новый заказ \\#{order.pk}*\n\n'
        f'📧 Email: `{order.email}`\n'
        f'📄 Документ: {_escape(order.document.title)}\n'
        f'💰 Сумма: *{order.document.price} ₸*\n'
        f'{payment_emoji} Оплата: {order.get_payment_method_display()}\n\n'
        f'Для управления используйте бот\\.'
    )

    url = f'https://api.telegram.org/bot{8694246532:AAFCXSrG_h630ad5ir4Y5Bq7_AFkZJ77r0c}/sendMessage'

    for admin_id in TELEGRAM_ADMIN_IDS:
        payload = {
            'chat_id': admin_id,
            'text': text,
            'parse_mode': 'MarkdownV2',
            'reply_markup': {
                'inline_keyboard': [[
                    {
                        'text': '✅ Подтвердить оплату',
                        'callback_data': f'confirm_{order.pk}'
                    },
                    {
                        'text': '❌ Отменить',
                        'callback_data': f'cancel_{order.pk}'
                    }
                ]]
            }
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if not response.ok:
                logger.error(
                    f'Telegram API error for admin {admin_id}: {response.text}'
                )
        except requests.RequestException as e:
            logger.error(f'Failed to send Telegram notification: {e}')


def _escape(text: str) -> str:
    """Экранирование спецсимволов для MarkdownV2."""
    special = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in special else c for c in str(text))
