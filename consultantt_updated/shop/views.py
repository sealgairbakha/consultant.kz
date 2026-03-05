from django.shortcuts import render
from django.conf import settings
from .models import Document


def index(request):
    documents = Document.objects.filter(is_active=True)
    context = {
        'documents': documents,
        'whatsapp_link': settings.WHATSAPP_LINK,
    }
    return render(request, 'index.html', context)
