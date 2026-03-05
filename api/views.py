import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from shop.models import Document, Order


@require_GET
def documents_list(request):
    documents = Document.objects.filter(is_active=True).values(
        'id', 'title', 'slug', 'description', 'price'
    )
    data = []
    for doc in documents:
        doc['price'] = str(doc['price'])
        data.append(doc)
    return JsonResponse({'documents': data})


@csrf_protect
@require_POST
def order_create(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Неверный формат данных.'}, status=400)

    email = body.get('email', '').strip()
    document_id = body.get('document_id')

    if not email:
        return JsonResponse({'error': 'Email обязателен.'}, status=400)

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'error': 'Некорректный email адрес.'}, status=400)

    if not document_id:
        return JsonResponse({'error': 'Выберите документ.'}, status=400)

    try:
        document = Document.objects.get(pk=document_id, is_active=True)
    except Document.DoesNotExist:
        return JsonResponse({'error': 'Документ не найден.'}, status=404)

    order = Order.objects.create(
        email=email,
        document=document,
        status=Order.STATUS_WAITING_PAYMENT,
    )

    return JsonResponse({
        'success': True,
        'order_id': order.pk,
        'status': order.status,
        'document_title': document.title,
        'price': str(document.price),
    }, status=201)


@csrf_protect
@require_POST
def order_confirm_payment(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Неверный формат данных.'}, status=400)

    order_id = body.get('order_id')

    if not order_id:
        return JsonResponse({'error': 'ID заказа обязателен.'}, status=400)

    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Заказ не найден.'}, status=404)

    if order.status not in [Order.STATUS_WAITING_PAYMENT, Order.STATUS_CREATED]:
        return JsonResponse({
            'error': 'Статус заказа не позволяет выполнить это действие.',
            'current_status': order.status,
        }, status=400)

    order.status = Order.STATUS_PAID
    order.save()

    return JsonResponse({
        'success': True,
        'order_id': order.pk,
        'status': order.status,
        'message': 'Оплата подтверждена. Ваш документ будет отправлен в течение 5–15 минут.',
    })
