import json as _json
import urllib.request

from rest_framework import viewsets, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Cliente, EnderecoCliente
from .serializers import ClienteSerializer, ClienteListSerializer, EnderecoClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'whatsapp', 'email']
    ordering_fields = ['nome', 'total_gasto', 'qtd_pedidos', 'ultima_compra']

    def get_serializer_class(self):
        if self.action == 'list':
            return ClienteListSerializer
        return ClienteSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        ativo = self.request.query_params.get('ativo')
        estado = self.request.query_params.get('estado')
        if ativo is not None:
            qs = qs.filter(ativo=ativo.lower() == 'true')
        if estado:
            qs = qs.filter(estado=estado.upper())
        return qs


class EnderecoClienteViewSet(viewsets.ModelViewSet):
    queryset = EnderecoCliente.objects.select_related('cliente')
    serializer_class = EnderecoClienteSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        return qs


@api_view(['GET'])
def buscar_cep(request, cep):
    cep_limpo = ''.join(c for c in cep if c.isdigit())
    if len(cep_limpo) != 8:
        return Response({'erro': 'CEP inválido.'}, status=400)
    try:
        url = f'https://viacep.com.br/ws/{cep_limpo}/json/'
        with urllib.request.urlopen(url, timeout=5) as resp:
            dados = _json.loads(resp.read())
        if dados.get('erro'):
            return Response({'erro': 'CEP não encontrado.'}, status=404)
        return Response({
            'cep': dados.get('cep', ''),
            'logradouro': dados.get('logradouro', ''),
            'complemento': dados.get('complemento', ''),
            'bairro': dados.get('bairro', ''),
            'cidade': dados.get('localidade', ''),
            'estado': dados.get('uf', ''),
        })
    except Exception:
        return Response({'erro': 'Erro ao consultar ViaCEP.'}, status=503)
