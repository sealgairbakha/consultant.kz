from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order
from .services import send_document_email


@receiver(post_save, sender=Order)
def on_order_created(sender, instance, created, **kwargs):
    """При создании нового заказа — уведомить администраторов в Telegram."""
    if created:
        try:
            from telegram_bot.notifier import send_telegram_notification
            send_telegram_notification(instance)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f'Telegram notification failed for order #{instance.pk}: {e}'
            )


@receiver(pre_save, sender=Order)
def on_order_status_change(sender, instance, **kwargs):
    """При переходе статуса → sent отправляем файл на email."""
    if not instance.pk:
        return

    try:
        previous = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    if previous.status != Order.STATUS_SENT and instance.status == Order.STATUS_SENT:
        send_document_email(instance)
