from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoriaFinanceiraViewSet,
    ContaPagarViewSet,
    ContaReceberViewSet,
    LancamentoCaixaViewSet,
    dre,
    fluxo_caixa,
)

router = DefaultRouter()
router.register('contas-receber', ContaReceberViewSet)
router.register('contas-pagar', ContaPagarViewSet)
router.register('categorias', CategoriaFinanceiraViewSet)
router.register('lancamentos', LancamentoCaixaViewSet)

urlpatterns = router.urls + [
    path('fluxo-caixa/', fluxo_caixa, name='fluxo-caixa'),
    path('dre/', dre, name='dre'),
]
