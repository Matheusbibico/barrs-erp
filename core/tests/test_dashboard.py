from django.contrib.auth.models import User
from django.test import TestCase


class DashboardViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            'staff', 'staff@test.com', 'pass', is_staff=True
        )

    def test_redireciona_usuario_anonimo(self):
        r = self.client.get('/dashboard/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/admin/login/', r['Location'])

    def test_renderiza_para_staff(self):
        self.client.force_login(self.staff)
        r = self.client.get('/dashboard/')
        self.assertEqual(r.status_code, 200)

    def test_context_contem_chaves_obrigatorias(self):
        self.client.force_login(self.staff)
        r = self.client.get('/dashboard/')
        chaves = [
            'faturamento_hoje', 'faturamento_mes', 'lucro_mes', 'pedidos_pendentes',
            'ticket_medio_mes', 'clientes_ativos', 'top5_produtos',
            'grafico_labels', 'grafico_dados', 'grafico_lucro',
            'vendas_canal_labels', 'vendas_canal_dados',
            'estoque_total_ativos', 'estoque_baixo_count', 'estoque_zerado_count',
        ]
        for chave in chaves:
            self.assertIn(chave, r.context, f'Context faltando: {chave}')
