import os
from django.core.mail import EmailMessage
from django.conf import settings


def send_document_email(order):
    """Send purchased document to the customer's email."""
    document = order.document
    subject = f'Ваш документ: {document.title}'
    body = (
        f'Здравствуйте!\n\n'
        f'Спасибо за покупку. Ваш заказ #{order.pk} подтверждён.\n\n'
        f'Документ: {document.title}\n'
        f'Стоимость: {document.price} ₸\n\n'
        f'Файл прикреплён к этому письму.\n\n'
        f'С уважением,\nКоманда Consultantt'
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )

    file_path = document.file.path
    if os.path.exists(file_path):
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            email.attach(file_name, f.read(), 'application/octet-stream')

    email.send(fail_silently=False)
