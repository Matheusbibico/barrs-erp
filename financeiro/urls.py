from rest_framework.routers import DefaultRouter
from .views import ContaReceberViewSet, ContaPagarViewSet

router = DefaultRouter()
router.register('contas-receber', ContaReceberViewSet)
router.register('contas-pagar', ContaPagarViewSet)

urlpatterns = router.urls
