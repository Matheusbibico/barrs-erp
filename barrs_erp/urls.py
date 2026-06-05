from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.views import dashboard, webhook_nova_venda

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', dashboard, name='dashboard'),
    path('webhook/nova-venda/', webhook_nova_venda, name='webhook_nova_venda'),
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
