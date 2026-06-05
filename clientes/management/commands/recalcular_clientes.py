from django.core.management.base import BaseCommand
from django.db.models import Max, Sum

from clientes.models import Cliente
from pedidos.models import Pedido

STATUSES_PAGOS = ['pago', 'enviado', 'entregue']


class Command(BaseCommand):
    help = 'Recalcula total_gasto, qtd_pedidos e ultima_compra para todos os clientes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cliente-id',
            type=int,
            help='Recalcular apenas um cliente específico',
        )

    def handle(self, *args, **options):
        qs = Cliente.objects.all()
        if options['cliente_id']:
            qs = qs.filter(pk=options['cliente_id'])

        total = qs.count()
        atualizados = 0

        self.stdout.write(f'Recalculando {total} clientes...')

        for cliente in qs.iterator():
            pedidos_qs = Pedido.objects.filter(
                cliente=cliente,
                status__in=STATUSES_PAGOS,
            )
            agg = pedidos_qs.aggregate(
                total=Sum('total_liquido'),
                ultima=Max('criado_em'),
            )
            novo_total = agg['total'] or 0
            novo_count = pedidos_qs.count()
            nova_ultima = agg['ultima'].date() if agg['ultima'] else None

            if (
                cliente.total_gasto != novo_total
                or cliente.qtd_pedidos != novo_count
                or cliente.ultima_compra != nova_ultima
            ):
                cliente.total_gasto = novo_total
                cliente.qtd_pedidos = novo_count
                cliente.ultima_compra = nova_ultima
                cliente.save(update_fields=['total_gasto', 'qtd_pedidos', 'ultima_compra'])
                atualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Concluído: {atualizados}/{total} clientes atualizados.'
        ))
