from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse  # ✅ добавили

def healthz(request):  # ✅ добавили
    return HttpResponse("ok")

urlpatterns = [
    path('healthz/', healthz),  # ✅ добавили
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('shop.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)