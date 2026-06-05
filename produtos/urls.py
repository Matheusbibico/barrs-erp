from rest_framework.routers import DefaultRouter
from .views import CategoriaViewSet, FornecedorViewSet, ProdutoViewSet, FotoProdutoViewSet

router = DefaultRouter()
router.register('categorias', CategoriaViewSet)
router.register('fornecedores', FornecedorViewSet)
router.register('fotos', FotoProdutoViewSet)
router.register('', ProdutoViewSet)

urlpatterns = router.urls
