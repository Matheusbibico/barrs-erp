from rest_framework.routers import DefaultRouter
from .views import PedidoViewSet, ItemPedidoViewSet, PagamentoViewSet, LucroPedidoViewSet, EventoRastreioViewSet

router = DefaultRouter()
router.register('itens', ItemPedidoViewSet)
router.register('pagamentos', PagamentoViewSet)
router.register('lucros', LucroPedidoViewSet)
router.register('eventos-rastreio', EventoRastreioViewSet)
router.register('', PedidoViewSet)

urlpatterns = router.urls
