from rest_framework.routers import DefaultRouter
from .views import MovimentoEstoqueViewSet

router = DefaultRouter()
router.register('movimentos', MovimentoEstoqueViewSet)

urlpatterns = router.urls
