from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include([
        path('produtos/', include('produtos.urls')),
        path('clientes/', include('clientes.urls')),
        path('pedidos/', include('pedidos.urls')),
        path('estoque/', include('estoque.urls')),
        path('financeiro/', include('financeiro.urls')),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
