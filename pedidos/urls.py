from rest_framework.routers import DefaultRouter
from .views import (
    PedidoViewSet, ItemPedidoViewSet, PagamentoViewSet,
    LucroPedidoViewSet, EventoRastreioViewSet, DevolucaoViewSet,
)

router = DefaultRouter()
router.register('itens', ItemPedidoViewSet)
router.register('pagamentos', PagamentoViewSet)
router.register('lucros', LucroPedidoViewSet)
router.register('eventos-rastreio', EventoRastreioViewSet)
router.register('devolucoes', DevolucaoViewSet)
router.register('', PedidoViewSet)

urlpatterns = router.urls
