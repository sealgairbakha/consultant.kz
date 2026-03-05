from django.db import models
from django.utils.text import slugify


class Document(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(unique=True, blank=True, verbose_name='Slug')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    file = models.FileField(upload_to='documents/', verbose_name='Файл документа')
    preview_image = models.ImageField(
        upload_to='previews/', blank=True, null=True, verbose_name='Превью'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['title']

    def __str__(self):
        return f'{self.title} — {self.price} ₸'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CREATED = 'created'
    STATUS_WAITING_PAYMENT = 'waiting_payment'
    STATUS_PAID = 'paid'
    STATUS_SENT = 'sent'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создан'),
        (STATUS_WAITING_PAYMENT, 'Ожидает оплаты'),
        (STATUS_PAID, 'Оплачен'),
        (STATUS_SENT, 'Отправлен'),
        (STATUS_CANCELLED, 'Отменён'),
    ]

    email = models.EmailField(verbose_name='Email покупателя')
    document = models.ForeignKey(
        Document, on_delete=models.PROTECT, related_name='orders', verbose_name='Документ'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.pk} — {self.email} — {self.get_status_display()}'
