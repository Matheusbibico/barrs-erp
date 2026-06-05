import json
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

GOOD_TOKEN = 'testtokenabcdef1234567890'


@override_settings(WEBHOOK_TOKEN=GOOD_TOKEN)
class WebhookAuthTests(TestCase):
    URL = '/webhook/nova-venda/'

    def post(self, body, token=GOOD_TOKEN, **extra):
        headers = {}
        if token is not None:
            headers['HTTP_X_WEBHOOK_TOKEN'] = token
        return self.client.post(
            self.URL,
            data=json.dumps(body),
            content_type='application/json',
            **headers,
            **extra,
        )

    def test_get_retorna_405(self):
        r = self.client.get(self.URL)
        self.assertEqual(r.status_code, 405)

    def test_sem_token_retorna_401(self):
        r = self.post({'pedido_id': 1}, token=None)
        self.assertEqual(r.status_code, 401)

    def test_token_errado_retorna_401(self):
        r = self.post({'pedido_id': 1}, token='tokenerrado')
        self.assertEqual(r.status_code, 401)

    def test_sem_pedido_id_retorna_400(self):
        r = self.post({})
        self.assertEqual(r.status_code, 400)

    def test_pedido_id_invalido_retorna_400(self):
        r = self.post({'pedido_id': 'abc'})
        self.assertEqual(r.status_code, 400)

    @override_settings(
        WEBHOOK_TOKEN=GOOD_TOKEN,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
    def test_sem_banco_site_retorna_503(self):
        r = self.post({'pedido_id': 1})
        self.assertEqual(r.status_code, 503)

    @override_settings(
        WEBHOOK_TOKEN=GOOD_TOKEN,
        DATABASES={
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
            'site': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        },
    )
    @patch('core.views._importar_pedido_unico')
    def test_requisicao_valida_retorna_200(self, mock_import):
        import uuid
        mock_pedido = MagicMock()
        mock_pedido.id = uuid.uuid4()
        mock_import.return_value = (mock_pedido, True)

        r = self.post({'pedido_id': 1})

        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content)
        self.assertEqual(data['status'], 'ok')
        self.assertTrue(data['criado'])

    @override_settings(
        WEBHOOK_TOKEN=GOOD_TOKEN,
        DATABASES={
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
            'site': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        },
    )
    @patch('core.views._importar_pedido_unico')
    def test_pedido_nao_encontrado_retorna_404(self, mock_import):
        from core.site_models import SitePedido
        mock_import.side_effect = SitePedido.DoesNotExist

        r = self.post({'pedido_id': 999})

        self.assertEqual(r.status_code, 404)


from decimal import Decimal

from clientes.models import Cliente
from pedidos.models import Pedido
from produtos.models import Produto


class ImportarPedidoUnicoTests(TestCase):
    def setUp(self):
        self.placeholder = Produto.objects.create(
            sku='SITE-DESCONHECIDO',
            nome='Produto não identificado (importado)',
            preco_venda=Decimal('0'),
            custo=Decimal('0'),
            status='inativo',
        )
        self.produto = Produto.objects.create(
            sku='P001',
            nome='Brinco Dourado',
            preco_venda=Decimal('50'),
            custo=Decimal('10'),
            estoque_total=10,
            site_id=7,
        )

    def _make_site_item(self, produto_site_id, quantidade, preco):
        item = MagicMock()
        item.produto_id = produto_site_id
        item.quantidade = quantidade
        item.preco_unitario = Decimal(str(preco))
        return item

    def _make_site_pedido(self, site_id=1, status='confirmado', itens=None):
        from django.utils import timezone
        sp = MagicMock()
        sp.id = site_id
        sp.nome = 'Ana Silva'
        sp.email = 'ana@test.com'
        sp.telefone = '11999999999'
        sp.cidade = 'São Paulo'
        sp.estado = 'SP'
        sp.status = status
        sp.subtotal = Decimal('100.00')
        sp.desconto = Decimal('0.00')
        sp.frete = Decimal('10.00')
        sp.total = Decimal('110.00')
        sp.criado_em = timezone.now()
        sp.itens.all.return_value = itens or []
        return sp

    @patch('core.views.SitePedido')
    def test_cria_pedido_e_cliente(self, MockSP):
        sp = self._make_site_pedido(site_id=100)
        MockSP.objects.using.return_value.prefetch_related.return_value.get.return_value = sp

        from core.views import _importar_pedido_unico
        pedido, criado = _importar_pedido_unico(100)

        self.assertTrue(criado)
        self.assertTrue(Cliente.objects.filter(email='ana@test.com').exists())
        self.assertTrue(Pedido.objects.filter(site_id=100).exists())
        self.assertEqual(pedido.status, Pedido.STATUS_PAGO)

    @patch('core.views.SitePedido')
    def test_idempotente_segunda_chamada(self, MockSP):
        sp = self._make_site_pedido(site_id=101)
        MockSP.objects.using.return_value.prefetch_related.return_value.get.return_value = sp

        from core.views import _importar_pedido_unico
        _, criado1 = _importar_pedido_unico(101)
        _, criado2 = _importar_pedido_unico(101)

        self.assertTrue(criado1)
        self.assertFalse(criado2)
        self.assertEqual(Pedido.objects.filter(site_id=101).count(), 1)

    @patch('core.views.SitePedido')
    def test_decrementa_estoque_do_produto(self, MockSP):
        item = self._make_site_item(produto_site_id=7, quantidade=3, preco='50.00')
        sp = self._make_site_pedido(site_id=102, itens=[item])
        MockSP.objects.using.return_value.prefetch_related.return_value.get.return_value = sp

        from core.views import _importar_pedido_unico
        _importar_pedido_unico(102)

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque_total, 7)  # 10 - 3

    @patch('core.views.SitePedido')
    def test_item_sem_produto_usa_placeholder(self, MockSP):
        item = self._make_site_item(produto_site_id=999, quantidade=1, preco='30.00')
        sp = self._make_site_pedido(site_id=103, itens=[item])
        MockSP.objects.using.return_value.prefetch_related.return_value.get.return_value = sp

        from core.views import _importar_pedido_unico
        pedido, _ = _importar_pedido_unico(103)

        item_ped = pedido.itens.first()
        self.assertEqual(item_ped.produto.sku, 'SITE-DESCONHECIDO')
