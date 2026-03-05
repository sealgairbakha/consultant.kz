import os
import sys
import logging
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'consultantt.settings')
django.setup()

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from django.utils.asyncio import sync_to_async
from asgiref.sync import sync_to_async
from shop.models import Order
from shop.services import send_document_email

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
ADMIN_IDS_RAW = os.environ.get('TELEGRAM_ADMIN_IDS', '')
ADMIN_IDS = [int(i.strip()) for i in ADMIN_IDS_RAW.split(',') if i.strip()]


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def build_order_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    buttons = []
    if status in [Order.STATUS_CREATED, Order.STATUS_WAITING_PAYMENT]:
        buttons.append([
            InlineKeyboardButton('✅ Подтвердить оплату', callback_data=f'confirm_{order_id}'),
            InlineKeyboardButton('❌ Отменить заказ', callback_data=f'cancel_{order_id}'),
        ])
    return InlineKeyboardMarkup(buttons) if buttons else None


def format_order_message(order: Order) -> str:
    return (
        f'🛒 *Новый заказ #{order.pk}*\n\n'
        f'📧 Email: `{order.email}`\n'
        f'📄 Документ: {order.document.title}\n'
        f'💰 Сумма: *{order.document.price} ₸*\n'
        f'💳 Оплата: Kaspi\n'
        f'📊 Статус: {order.get_status_display()}\n'
    )


@sync_to_async
def get_pending_orders():
    return list(
        Order.objects.filter(
            status__in=[Order.STATUS_CREATED, Order.STATUS_WAITING_PAYMENT]
        ).select_related('document').order_by('-created_at')[:20]
    )


@sync_to_async
def get_order(order_id):
    try:
        return Order.objects.select_related('document').get(pk=order_id)
    except Order.DoesNotExist:
        return None


@sync_to_async
def confirm_order(order):
    send_document_email(order)
    order.status = Order.STATUS_SENT
    order.save()


@sync_to_async
def set_order_status(order, status):
    order.status = status
    order.save()


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('⛔ Доступ запрещён.')
        return
    await update.message.reply_text(
        '👋 Привет! Я бот для управления заказами Consultantt.\n\n'
        'Команды:\n'
        '/orders — список ожидающих оплаты\n'
        '/order <id> — информация о заказе'
    )


async def cmd_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('⛔ Доступ запрещён.')
        return

    pending = await get_pending_orders()

    if not pending:
        await update.message.reply_text('✅ Нет ожидающих заказов.')
        return

    for order in pending:
        text = format_order_message(order)
        keyboard = build_order_keyboard(order.pk, order.status)
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)


async def cmd_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('⛔ Доступ запрещён.')
        return

    if not context.args:
        await update.message.reply_text('Использование: /order <id>')
        return

    try:
        order_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text('❌ Неверный ID.')
        return

    order = await get_order(order_id)
    if not order:
        await update.message.reply_text('❌ Заказ не найден.')
        return

    text = format_order_message(order)
    keyboard = build_order_keyboard(order.pk, order.status)
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text('⛔ Доступ запрещён.')
        return

    data = query.data
    if data.startswith('confirm_'):
        order_id = int(data.split('_')[1])
        await process_confirm(query, order_id)
    elif data.startswith('cancel_'):
        order_id = int(data.split('_')[1])
        await process_cancel(query, order_id)


async def process_confirm(query, order_id: int) -> None:
    order = await get_order(order_id)
    if not order:
        await query.edit_message_text('❌ Заказ не найден.')
        return

    if order.status not in [Order.STATUS_CREATED, Order.STATUS_WAITING_PAYMENT]:
        await query.edit_message_text(
            f'⚠️ Заказ #{order_id} уже обработан.\nТекущий статус: {order.get_status_display()}'
        )
        return

    try:
        await confirm_order(order)
        await query.edit_message_text(
            f'✅ *Заказ #{order_id} подтверждён!*\n\n'
            f'📧 Документ отправлен на `{order.email}`\n'
            f'📄 {order.document.title}',
            parse_mode='Markdown'
        )
        logger.info(f'Order #{order_id} confirmed and sent to {order.email}')
    except Exception as e:
        logger.error(f'Failed to send email for order #{order_id}: {e}')
        await set_order_status(order, Order.STATUS_PAID)
        await query.edit_message_text(
            f'⚠️ *Заказ #{order_id} отмечен как оплаченный*, но письмо не отправлено!\n\n'
            f'Ошибка: `{e}`\n\n'
            f'Используйте /order {order_id} для повторной отправки.',
            parse_mode='Markdown'
        )


async def process_cancel(query, order_id: int) -> None:
    order = await get_order(order_id)
    if not order:
        await query.edit_message_text('❌ Заказ не найден.')
        return

    if order.status in [Order.STATUS_PAID, Order.STATUS_SENT]:
        await query.edit_message_text(
            f'⚠️ Нельзя отменить заказ #{order_id} — он уже {order.get_status_display().lower()}.'
        )
        return

    await set_order_status(order, Order.STATUS_CANCELLED)
    await query.edit_message_text(
        f'❌ *Заказ #{order_id} отменён.*\n\nEmail: `{order.email}`',
        parse_mode='Markdown'
    )
    logger.info(f'Order #{order_id} cancelled by admin')


def main() -> None:
    if not BOT_TOKEN:
        logger.error('TELEGRAM_BOT_TOKEN не задан!')
        sys.exit(1)
    if not ADMIN_IDS:
        logger.error('TELEGRAM_ADMIN_IDS не задан!')
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('orders', cmd_orders))
    app.add_handler(CommandHandler('order', cmd_order))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info(f'Бот запущен. Администраторы: {ADMIN_IDS}')
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()