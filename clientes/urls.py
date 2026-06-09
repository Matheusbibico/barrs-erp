from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ClienteViewSet, EnderecoClienteViewSet, buscar_cep

router = DefaultRouter()
router.register('enderecos', EnderecoClienteViewSet)
router.register('', ClienteViewSet)

urlpatterns = router.urls + [
    path('cep/<str:cep>/', buscar_cep, name='buscar_cep'),
]
