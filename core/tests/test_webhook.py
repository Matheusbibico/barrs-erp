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
