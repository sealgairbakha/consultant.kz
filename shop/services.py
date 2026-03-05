import os
import httpx
from django.core.mail import EmailMessage
from django.conf import settings


def send_document_email(order):
    document = order.document
    subject = f'Ваш документ: {document.title}'
    body = (
        f'Здравствуйте!\n\n'
        f'Спасибо за покупку. Ваш заказ #{order.pk} подтверждён.\n\n'
        f'Документ: {document.title}\n'
        f'Стоимость: {document.price} тенге\n\n'
        f'Файл прикреплён к этому письму.\n\n'
        f'С уважением,\nКоманда Consultantt'
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )

    file_url = document.file.url
    file_name = os.path.basename(file_url.split('?')[0])
    response = httpx.get(file_url, timeout=30)
    response.raise_for_status()
    email.attach(file_name, response.content, 'application/octet-stream')

    email.send(fail_silently=False)
