from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

import pedidos.signals as pedido_signals
from clientes.models import Cliente
from core.site_models import (
    SiteCategoria, SiteItemPedido, SitePedido,
    SitePerfilCliente, SiteProduto, SiteUser,
)
from pedidos.models import ItemPedido, Pagamento, Pedido
from produtos.models import Categoria, Produto

STATUS_MAP = {
    'pendente': Pedido.STATUS_AGUARDANDO,
    'confirmado': Pedido.STATUS_PAGO,
    'enviado': Pedido.STATUS_ENVIADO,
    'entregue': Pedido.STATUS_ENTREGUE,
    'cancelado': Pedido.STATUS_CANCELADO,
}


class Command(BaseCommand):
    help = 'Importa produtos, clientes e pedidos do banco secundário do site Django'

    def handle(self, *args, **options):
        if 'site' not in settings.DATABASES:
            self.stderr.write(self.style.ERROR(
                'Banco "site" não configurado. Defina SITE_DATABASE_URL.'
            ))
            return

        post_save.disconnect(pedido_signals.atualizar_historico_cliente, sender=Pedido)
        try:
            stats = {
                'categorias': self._importar_categorias(),
                'produtos':   self._importar_produtos(),
                'clientes':   self._importar_clientes(),
                'pedidos':    self._importar_pedidos(),
            }
        finally:
            post_save.connect(pedido_signals.atualizar_historico_cliente, sender=Pedido)
        self._relatorio(stats)

    def _importar_categorias(self):
        self.stdout.write('Importando categorias...')
        criadas = atualizadas = erros = 0
        for sc in SiteCategoria.objects.using('site').all():
            try:
                cat, created = Categoria.objects.get_or_create(
                    nome=sc.nome,
                )
                if created:
                    criadas += 1
                else:
                    atualizadas += 1
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  Categoria {sc.nome}: {exc}'))
                erros += 1
        return {'criadas': criadas, 'atualizadas': atualizadas, 'erros': erros}

    def _importar_produtos(self):
        self.stdout.write('Importando produtos...')
        criados = atualizados = erros = 0
        cat_map = {c.nome: c for c in Categoria.objects.all()}

        Produto.objects.get_or_create(
            sku='SITE-DESCONHECIDO',
            defaults={
                'nome': 'Produto não identificado (importado)',
                'preco_venda': Decimal('0'),
                'custo': Decimal('0'),
                'status': Produto.STATUS_INATIVO,
            },
        )

        for sp in SiteProduto.objects.using('site').select_related('categoria'):
            try:
                sku = (sp.codigo_interno or '').strip() or f'SITE-{sp.id}'
                status = Produto.STATUS_ATIVO if sp.visivel else Produto.STATUS_INATIVO
                cat = cat_map.get(sp.categoria.nome) if sp.categoria else None

                prod, created = Produto.objects.get_or_create(
                    site_id=sp.id,
                    defaults={
                        'sku': sku,
                        'nome': sp.nome,
                        'preco_venda': sp.preco,
                        'custo': Decimal('0'),
                        'estoque_total': sp.estoque,
                        'categoria': cat,
                        'status': status,
                    },
                )
                if created:
                    criados += 1
                else:
                    prod.nome = sp.nome
                    prod.preco_venda = sp.preco
                    prod.estoque_total = sp.estoque
                    prod.status = status
                    prod.categoria = cat
                    prod.save(update_fields=['nome', 'preco_venda', 'estoque_total', 'status', 'categoria'])
                    atualizados += 1
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  Produto site_id={sp.id}: {exc}'))
                erros += 1
        return {'criadas': criados, 'atualizadas': atualizados, 'erros': erros}

    def _importar_clientes(self):
        self.stdout.write('Importando clientes...')
        criados = atualizados = erros = 0
        for su in SiteUser.objects.using('site').all():
            try:
                try:
                    perfil = SitePerfilCliente.objects.using('site').get(user_id=su.id)
                    whatsapp, cidade, estado = perfil.telefone, perfil.cidade, perfil.estado
                except SitePerfilCliente.DoesNotExist:
                    whatsapp = cidade = estado = ''

                nome = f'{su.first_name} {su.last_name}'.strip() or su.email
                cli, created = Cliente.objects.get_or_create(
                    site_id=su.id,
                    defaults={
                        'nome': nome, 'email': su.email,
                        'whatsapp': whatsapp, 'cidade': cidade, 'estado': estado,
                    },
                )
                if created:
                    criados += 1
                else:
                    cli.nome = nome
                    cli.email = su.email
                    cli.whatsapp = whatsapp
                    cli.save(update_fields=['nome', 'email', 'whatsapp'])
                    atualizados += 1
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  User site_id={su.id}: {exc}'))
                erros += 1
        return {'criadas': criados, 'atualizadas': atualizados, 'erros': erros}

    def _importar_pedidos(self):
        self.stdout.write('Importando pedidos...')
        criados = atualizados = erros = 0
        prod_map = {p.site_id: p for p in Produto.objects.filter(site_id__isnull=False)}
        placeholder = Produto.objects.get(sku='SITE-DESCONHECIDO')
        cli_email_map = {c.email: c for c in Cliente.objects.exclude(email='')}

        for sp in SitePedido.objects.using('site').prefetch_related('itens__produto'):
            try:
                status_erp = STATUS_MAP.get(sp.status, Pedido.STATUS_ORCAMENTO)
                cliente = cli_email_map.get(sp.email)
                if not cliente:
                    cliente, _ = Cliente.objects.get_or_create(
                        email=sp.email,
                        defaults={
                            'nome': sp.nome or sp.email,
                            'whatsapp': sp.telefone,
                            'cidade': sp.cidade,
                            'estado': sp.estado,
                        },
                    )
                    if sp.email:
                        cli_email_map[sp.email] = cliente

                ped, created = Pedido.objects.get_or_create(
                    site_id=sp.id,
                    defaults={
                        'cliente': cliente,
                        'canal': Pedido.CANAL_SITE,
                        'status': status_erp,
                        'total_bruto': sp.subtotal,
                        'desconto': sp.desconto,
                        'frete': sp.frete,
                        'total_liquido': sp.total,
                    },
                )
                if created:
                    criados += 1
                    for si in sp.itens.all():
                        produto = prod_map.get(si.produto_id) if si.produto_id else placeholder
                        ItemPedido.objects.create(
                            pedido=ped,
                            produto=produto or placeholder,
                            quantidade=si.quantidade,
                            preco_unitario=si.preco_unitario,
                            custo_unitario=Decimal('0'),
                        )
                    if status_erp == Pedido.STATUS_PAGO:
                        Pagamento.objects.get_or_create(
                            pedido=ped,
                            defaults={
                                'metodo': Pagamento.METODO_PIX,
                                'valor': sp.total,
                                'status': Pagamento.STATUS_APROVADO,
                            },
                        )
                else:
                    ped.status = status_erp
                    ped.total_liquido = sp.total
                    ped.save(update_fields=['status', 'total_liquido'])
                    atualizados += 1
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  Pedido site_id={sp.id}: {exc}'))
                erros += 1
        return {'criadas': criados, 'atualizadas': atualizados, 'erros': erros}

    def _relatorio(self, stats):
        labels = {
            'categorias': 'Categorias',
            'produtos':   'Produtos  ',
            'clientes':   'Clientes  ',
            'pedidos':    'Pedidos   ',
        }
        self.stdout.write('\n' + self.style.SUCCESS('Relatório final:'))
        for key, label in labels.items():
            s = stats.get(key, {})
            c, a, e = s.get('criadas', 0), s.get('atualizadas', 0), s.get('erros', 0)
            cor = self.style.SUCCESS if e == 0 else self.style.WARNING
            self.stdout.write(cor(f'  {label}: {c} criadas | {a} atualizadas | {e} erros'))
