from rest_framework.routers import DefaultRouter
from .views import (
    PedidoViewSet, ItemPedidoViewSet, PagamentoViewSet, DevolucaoViewSet,
)

router = DefaultRouter()
router.register('itens', ItemPedidoViewSet)
router.register('pagamentos', PagamentoViewSet)
router.register('devolucoes', DevolucaoViewSet)
router.register('', PedidoViewSet)

urlpatterns = router.urls
