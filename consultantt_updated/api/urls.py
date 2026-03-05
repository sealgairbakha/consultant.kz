from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('documents/', views.documents_list, name='documents-list'),
    path('orders/create/', views.order_create, name='order-create'),
    path('orders/confirm-payment/', views.order_confirm_payment, name='order-confirm-payment'),
]
